# BTRFdom - Rappelz BTRF Document Object Model
# By Glandu2/Peakz
# Copyright 2013 Glandu2
#
# This file is part of BTRFdom.
# BTRFdom is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BTRFdom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with BTRFdom.  If not, see <http://www.gnu.org/licenses/>.
#

""" NAF structure:
	template nx3_version_header {
		dword	version;
	}
	template nx3_bone_ani_header
	{E8F9296B-B9DD-4080-8BC7-6C69E0AA3FEB}
	{
		dword bone_count;
		dword channel_count;
		nx3_bone_ani_channel channel_array[channel_count];
	}
	template nx3_bone_ani_channel
	{81B3C137-B2B8-40b0-A3AD-D149467F5932}
	{
		string  channel_name;
		dword	channel_flag;
		dword   channel_time_span;
		dword   channel_frame_rate;
		
		dword		 bone_ani_size;
		nx3_bone_ani bone_ani_array[bone_ani_size];
	}
	template nx3_bone_ani
	{B84344DE-A1B6-4aa7-AFD6-22CA8A4B0CEE}
	{
		string  szName;
		dword	parent_Index;
		float	base_tm[16];
		dword	flag;

		dword   pos_time_size;
		dword   pos_time_array[pos_time_size];	
		dword	pos_key_size;
		float	pos_key_array[pos_key_size];
		
		dword   rot_time_size;	
		dword   rot_time_array[rot_time_size];	
		dword	rot_key_size;	
		float	rot_key_array[rot_key_size];
		dword	child_size;	
		dword	child_Index_array[child_size];
	}
    
"""

import bpy
import bmesh
import uuid
import mathutils
from .btrfdom import BtrfParser, TmlFile
import os
from mathutils import Matrix

nx3_version_header_guid = uuid.UUID('{81BCE021-AD76-346f-9C7D-19885FD118B6}')

nx3_bone_ani_header_guid = uuid.UUID('{E8F9296B-B9DD-4080-8BC7-6C69E0AA3FEB}')

nx3_bone_ani_channel_guid = uuid.UUID('{81B3C137-B2B8-40b0-A3AD-D149467F5932}')

nx3_bone_ani_guid = uuid.UUID('{B84344DE-A1B6-4aa7-AFD6-22CA8A4B0CEE}')

def info(str):
	print(('btrfdom: Info: ' + str))


def warn(str):
	print(('btrfdom: Warning: ' + str))


def error(str):
	print(('btrfdom: Error: ' + str))
	raise(str)


def check_version(rootBlock):
	block = rootBlock.getBlockByGuid(nx3_version_header_guid.bytes_le)

	if block:
		version = block.getBlock(0).getDataInt(0)
	else:
		info('there was no version information in this file')
		version = 0

	if version != 65536:
		warn('The version is not 65536, the model may not be read correctly')

def time_to_frame(time):
	return int(time / 5000 * 31.5 * bpy.context.scene.render.fps_base)

def read_bone_ani(nx3_bone_ani, armature, parents_only):

	name = nx3_bone_ani.getBlock(0).getDataString(0)
	#print(name)

	parent_index = nx3_bone_ani.getBlock(1).getDataInt(0)
	#print(parent_index)


	pos_time_array = [nx3_bone_ani.getBlock(4).getDataInt(i) for i in range(nx3_bone_ani.getBlock(4).getElementNumber())]
	pos_key_array = [nx3_bone_ani.getBlock(5).getDataFloat(i) for i in range(nx3_bone_ani.getBlock(5).getElementNumber())]
	rot_time_array = [nx3_bone_ani.getBlock(6).getDataInt(i) for i in range(nx3_bone_ani.getBlock(6).getElementNumber())]
	rot_key_array = [nx3_bone_ani.getBlock(7).getDataFloat(i) for i in range(nx3_bone_ani.getBlock(7).getElementNumber())]
	
	child_Index_array = [nx3_bone_ani.getBlock(8).getDataInt(i) for i in range(nx3_bone_ani.getBlock(8).getElementNumber())]
	
	
	if name not in armature.pose.bones and name.replace(' ','_') not in armature.pose.bones and name.replace('@','_') not in armature.pose.bones:
		return print(f"{name} not found")
	
	if name.replace(' ','_') in armature.pose.bones:
		name = name.replace(' ','_')
	
	if name.replace('@','_') in armature.pose.bones:
		name = name.replace('@','_')

	if parents_only and parent_index != -1:
		armature.data.edit_bones[name].use_connect = False
		armature.data.edit_bones[name].parent = armature.data.edit_bones[parent_index]
	
	for bn in armature.pose.bones:
		if bn.name == name:
			print(bn.name)
			bone = bn

	bone.rotation_mode = 'QUATERNION'
	t, q, s = bone.matrix.decompose()

	#'''
	if not parents_only:
		for i, time in enumerate(pos_time_array):
			time = int(time / 160)

			#print(bone.matrix)

			q[0], q[1], q[2], q[3] = rot_key_array[i*4+3], rot_key_array[i*4], rot_key_array[i*4+1], rot_key_array[i*4+2]
			t[0], t[1], t[2] = pos_key_array[i*3], pos_key_array[i*3+1], pos_key_array[i*3+2]
			T = Matrix.Translation(t)

			R = q.to_matrix().to_4x4()

			S = Matrix.Diagonal(s.to_4d())

			M = T @ R @ S
			#print(M)

			bone.matrix = M
			#bpy.context.view_layer.update()

			bone.keyframe_insert('location', frame=time)
			bone.keyframe_insert('rotation_quaternion', frame=time)
	
	#'''
	if not parents_only:
		bpy.context.scene.frame_start = int(pos_time_array[0] / 160)
		bpy.context.scene.frame_end = time_to_frame(pos_time_array[len(pos_time_array) - 1])
	
def read_ani_header(rootBlock, filename):
	nx3_bone_ani_channel_block = rootBlock.getBlockByGuid(nx3_bone_ani_header_guid.bytes_le)

	bone_count = nx3_bone_ani_channel_block.getBlock(0).getDataInt(0)
	print(bone_count)
	channel_array = nx3_bone_ani_channel_block.getBlock(1).getBlock(0)

	channel_name = channel_array.getBlock(0).getDataString(0)
	#print(channel_name)
	channel_flag = channel_array.getBlock(1).getDataInt(0)
	#print(channel_flag)
	channel_time_span = channel_array.getBlock(2).getDataInt(0)
	#print(channel_time_span)
	channel_frame_rate = channel_array.getBlock(3).getDataInt(0)
	#print(channel_frame_rate)
	bone_ani_array = channel_array.getBlock(4)

	if bpy.context.active_object != None and bpy.context.active_object.type == 'ARMATURE':
		armature = bpy.context.active_object
		new_armature = armature.copy()
		new_armature.data = new_armature.data.copy()
		bpy.context.collection.objects.link(new_armature)
	else:
		print("Please select the armature")
		return

	nx3_bone_ani_blocks = [bone_ani_array.getBlock(i) for i in range(bone_ani_array.getElementNumber())]

	bpy.ops.object.mode_set(mode = 'EDIT')
	for nx3_bone_ani in nx3_bone_ani_blocks:
		read_bone_ani(nx3_bone_ani, armature, True)	
		read_bone_ani(nx3_bone_ani, new_armature, False)	

	bpy.ops.object.mode_set(mode = 'OBJECT')

	#'''
	for bone in armature.pose.bones:
		constraint = bone.constraints.new('COPY_TRANSFORMS')
		constraint.target = new_armature
		constraint.subtarget = bone.name

	new_armature.select_set(False)
	armature.select_set(True)

	bpy.ops.nla.bake(
	frame_start=bpy.context.scene.frame_start,
	frame_end=bpy.context.scene.frame_end,
	only_selected=False,
	visual_keying=True,
	clear_constraints=True,
	clear_parents=False,
	bake_types={'POSE'}
	)

	bpy.data.objects.remove(new_armature, do_unlink=True)
	#'''


def read_naf_file(parser, naf_filename):
	info("Reading file %s" % naf_filename)

	rootBlock = parser.readFile(naf_filename)

	if rootBlock is None:
		error("Could not read nx3 file")
		return

	#check_version(rootBlock)
	
	return read_ani_header(rootBlock, os.path.basename(naf_filename))


def read(naf_filename):
	script_dir = os.path.dirname(os.path.abspath(__file__))

	tmlFile = TmlFile()
	tmlFile.create()
	tmlFile.parseFile(script_dir + "/nx3.tml")
	tmlFile.parseFile(script_dir + "/nobj.tml")

	parser = BtrfParser()
	parser.create(tmlFile)

	read_naf_file(parser, naf_filename)
