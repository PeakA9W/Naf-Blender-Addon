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
import uuid
from .btrfdom import BtrfParser, TmlFile, BtrfRootBlock, BtrfBlock
import os

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



def load_btrfdom():
	#Load the BTRFdom dll (or so on linux)
	script_dir = os.path.dirname(os.path.abspath(__file__))

	#Create a TmlFile object that will contain all known templates and their fields
	tmlFile = TmlFile()
	tmlFile.create()

	#Read some template files
	tmlFile.parseFile(script_dir + "/nx3.tml")
	tmlFile.parseFile(script_dir + "/nobj.tml")

	#Create a root block, it will contain all block in the btrf file (it does not exist in the file, it's here only to represent the file with all its blocks)
	rootBlock = BtrfRootBlock()
	rootBlock.create(tmlFile)

	return (tmlFile, rootBlock)


#version
def write_version(tmlFile, rootBlock):
	fieldInfo = tmlFile.getTemplateByGuid(nx3_version_header_guid.bytes_le)

	#Create a block that will contain the data of the template
	block = BtrfBlock()
	block.create(fieldInfo, rootBlock)

	#dword version
	subBlockInfo = fieldInfo.getField(0)
	subBlock = BtrfBlock()
	subBlock.create(subBlockInfo, rootBlock)
	subBlock.setDataInt(0, 65536)

	block.addBlock(subBlock)

	rootBlock.addBlock(block)

def get_bone_ani(tmlFile, rootBlock, armature, bone, frames):
	#Create a block that will contain the data of the template
	fieldInfo = tmlFile.getTemplateByGuid(nx3_bone_ani_guid.bytes_le)

	block = BtrfBlock()
	block.create(fieldInfo, rootBlock)

	#String szName (bone_name)
	szName = bone.name

	#DWord parent_Index
	if bone.parent:
		parent_bone = bone.parent
		for i, bn in enumerate(armature.pose.bones):
			if bn.name == parent_bone.name:
				parent_Index = i
	else:
		parent_Index = -1
	#Float base_tm
	base_tm = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

	#DWord flag
	flag = 0

	#arrays
	pos_time_array = []
	pos_key_array = []

	rot_time_array = []
	rot_key_array = []

	Scene = bpy.data.scenes['Scene']
	
	for frame in range(frames):
		
		Scene.frame_set(frame, subframe=0.0)
		add = 0
		if frame != 0:
			add = int((frame - 1) / 6)

		pos_time = frame * 160 + add
		
		rot_time = frame * 160 + add

		pos_key = bone.matrix.translation

		bone_quaternion = bone.matrix.to_quaternion()
		rot_key = [bone_quaternion[1], bone_quaternion[2], bone_quaternion[3], bone_quaternion[0]]

		pos_time_array.append(pos_time)
		rot_time_array.append(rot_time)

		for i in range(3):
			pos_key_array.append(pos_key[i])

		for i in range(4):
			rot_key_array.append(rot_key[i])



    #Dword child_Index_array
	bone_children = bone.children
	child_Index_array = []
	for bone in bone_children:
		for i, bn in enumerate(armature.pose.bones):
			if bn.name == bone.name:
				child_Index_array.append(i)

	
	#String szName
	subBlock = BtrfBlock()
	subBlock.create(fieldInfo.getField(0), rootBlock)
	subBlock.setDataString(0, szName)
	block.addBlock(subBlock)

	#DWord parent_Index
	subBlock.create(fieldInfo.getField(1), rootBlock)
	subBlock.setDataInt(0, parent_Index)
	block.addBlock(subBlock)

	#Float base_tm
	subBlock.create(fieldInfo.getField(2), rootBlock)
	for i in range(len(base_tm)):
		subBlock.setDataFloat(i, base_tm[i])
	block.addBlock(subBlock)

	#DWord flag
	subBlock.create(fieldInfo.getField(3), rootBlock)
	subBlock.setDataInt(0, flag)
	block.addBlock(subBlock)


	#DWord pos_time_array
	subBlock.create(fieldInfo.getField(4), rootBlock)
	subBlock.setElementNumber(len(pos_time_array))

	for i in range(len(pos_time_array)):
		subBlock.setDataInt(i, pos_time_array[i])
	block.addBlock(subBlock)
	
	#Float pos_key_array
	subBlock.create(fieldInfo.getField(5), rootBlock)
	subBlock.setElementNumber(len(pos_key_array))
	for i in range(len(pos_key_array)):
		subBlock.setDataFloat(i, pos_key_array[i])
	block.addBlock(subBlock)

	#DWord rot_time_array
	subBlock.create(fieldInfo.getField(6), rootBlock)
	subBlock.setElementNumber(len(rot_time_array))
	for i in range(len(rot_time_array)):
		subBlock.setDataInt(i, rot_time_array[i])
	block.addBlock(subBlock)

	#Float rot_key_array
	subBlock.create(fieldInfo.getField(7), rootBlock)
	subBlock.setElementNumber(len(rot_key_array))
	for i in range(len(rot_key_array)):
		subBlock.setDataFloat(i, rot_key_array[i])
	block.addBlock(subBlock)
	
	#DWord child_Index_array
	subBlock.create(fieldInfo.getField(8), rootBlock)
	subBlock.setElementNumber(len(child_Index_array))
	for i in range(len(child_Index_array)):
		subBlock.setDataInt(i, child_Index_array[i])
	block.addBlock(subBlock)
	
	return block


def get_bone_ani_channel(tmlFile, rootBlock, armature):
	#Create a block that will contain the data of the template
	fieldInfo = tmlFile.getTemplateByGuid(nx3_bone_ani_channel_guid.bytes_le)

	block = BtrfBlock()
	block.create(fieldInfo, rootBlock)

	channel_name = '<NULL>'
	channel_flag = 0

	Scene = bpy.data.scenes['Scene']
	frames = len(range(Scene.frame_start, Scene.frame_end + 1))
	channel_time_span = frames * 160 + int((frames - 1) / 6)  

	channel_frame_rate = 0

	subBlock = BtrfBlock()

	#String channel_name
	subBlock.create(fieldInfo.getField(0), rootBlock)
	subBlock.setDataString(0, channel_name)
	block.addBlock(subBlock)

	#DWord channel_flag
	subBlock.create(fieldInfo.getField(1), rootBlock)

	subBlock.setDataInt(0, channel_flag)
	block.addBlock(subBlock)

	#DWord channel_time_span
	subBlock.create(fieldInfo.getField(2), rootBlock)
	subBlock.setDataInt(0, channel_time_span)
	block.addBlock(subBlock)

	#DWord channel_frame_rate
	subBlock.create(fieldInfo.getField(3), rootBlock)
	subBlock.setDataInt(0, channel_frame_rate)
	block.addBlock(subBlock)
	
	#Array bone_ani_array
	arrayBlock = BtrfBlock()
	arrayBlock.create(fieldInfo.getField(4), rootBlock)
	for bone in armature.pose.bones:
		subBlock = get_bone_ani(tmlFile, rootBlock, armature, bone, frames)
		arrayBlock.addBlock(subBlock)

	block.addBlock(arrayBlock)
	
	return block


def write_bone_ani_header(tmlFile, rootBlock):
	fieldInfo = tmlFile.getTemplateByGuid(nx3_bone_ani_header_guid.bytes_le)

	#Create a block that will contain the data of the template
	block = BtrfBlock()
	block.create(fieldInfo, rootBlock)

	if bpy.context.active_object != None and bpy.context.active_object.type == 'ARMATURE':
		armature = bpy.context.active_object 
	else:
		print("Please select the armature")
		return
	
	bone_count = len(armature.pose.bones)
	print(bone_count)

	subBlock = BtrfBlock()
	
	#DWord bone_count
	subBlock.create(fieldInfo.getField(0), rootBlock)
	subBlock.setDataInt(0, bone_count)
	block.addBlock(subBlock)

	arrayBlock = BtrfBlock()
	arrayBlock.create(fieldInfo.getField(1), rootBlock)
	subBlock = get_bone_ani_channel(tmlFile, rootBlock, armature)
	arrayBlock.addBlock(subBlock)
	block.addBlock(arrayBlock)

	rootBlock.addBlock(block)


def write(filename):
	(tmlFile, rootBlock) = load_btrfdom()

	write_version(tmlFile, rootBlock)
	write_bone_ani_header(tmlFile, rootBlock)

	info("Writing file %s" % filename)
	writer = BtrfParser()
	writer.create(tmlFile)
	writer.writeFile(filename, rootBlock)
