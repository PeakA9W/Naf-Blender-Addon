# By Peakz

"""
Headers:
struct KFILEHEADER {
	char masterid[4] = "DIFK";
	char type[4] = "NIBK";
	int master_version = 1;
	int sub_version = 0;
	int nblocks;
	char reserved[108];
}

struct KFILEBLOCK {
	char blockid[4] = "KLBK";
	int blocksize;
	char reserved[24];
}

block:

enum MagicType {
	CLASSTYPEID_NONE = 0x00,
	CLASSTYPEID_WORD = 0x28,
	CLASSTYPEID_DWORD = 0x29,
	CLASSTYPEID_FLOAT = 0x2A,
	CLASSTYPEID_CHAR = 0x2C,
	CLASSTYPEID_UCHAR = 0x2D,
	CLASSTYPEID_STRING = 0x33,
	CLASSTYPEID_ARRAY = 0x34,
	CLASSTYPEID_TEMPLATE = 0x1F
}

struct GUID {
	char raw[16];
};	//see _GUID structure at msdn

struct Template_Element_t {
	MagicType magic = CLASSTYPEID_TEMPLATE;
	GUID guid;
	int array_elements_number;
	array_element_type elements[array_elements_number];
}

struct UChar_Element_t {
	MagicType magic = CLASSTYPEID_UCHAR;
	unsigned char value;
}

struct Char_Element_t {
	MagicType magic = CLASSTYPEID_CHAR;
	char value;
}

struct Float_Element_t {
	MagicType magic = CLASSTYPEID_FLOAT;
	float value;
}

struct Int_Element_t {
	MagicType magic = CLASSTYPEID_DWORD;
	int value;
}

struct Word_Element_t {
	MagicType magic = CLASSTYPEID_WORD;
	short value;
}

struct String_Element_t {
	MagicType magic = CLASSTYPEID_STRING;
	int string_size;
	char string_data[string_size];
}

struct Array_Element_t {
	MagicType magic = CLASSTYPEID_ARRAY;
	MagicType array_type_magic;
	int array_elements_number;
	String_Element_t size_field_name;	//no magic for this string
	array_element_type elements[array_elements_number];
}

struct TemplateArray_Element_t {
	MagicType magic = CLASSTYPEID_ARRAY;
	MagicType array_type_magic = CLASSTYPEID_TEMPLATE;
	GUID template_guid;
	int array_elements_number;
	String_Element_t size_field_name;	//no magic for this string
	array_element_type elements[array_elements_number];
}

"""
from struct import unpack
from mathutils import Matrix
import uuid
import bpy

nx3_bone_ani_header_guid = 'E8F9296B-B9DD-4080-8BC7-6C69E0AA3FEB'

nx3_bone_ani_channel_guid = '81B3C137-B2B8-40b0-A3AD-D149467F5932'

nx3_bone_ani_guid = 'B84344DE-A1B6-4aa7-AFD6-22CA8A4B0CEE'


def readType(file):
	x = file.read(1)
	if x == b'\x00':
		type = 'NONE'
	if x == b'\x28':
		type = 'WORD'
	if x == b'\x29':
		type = 'DWORD'
	if x == b'\x2A':
		type = 'FLOAT'
	if x == b'\x2C':
		type = 'CHAR'
	if x == b'\x2D':
		type = 'UCHAR'
	if x == b'\x33':
		type = 'STRING'
	if x == b'\x34':
		type = 'ARRAY'
	if x == b'\x1F':
		type = 'TEMPLATE'
	return type

def readChar(file):
	data = file.read(1)
	return unpack("c",data)[0]

def readInt(file):
    data = file.read(4)
    return unpack("i",data)[0]

def readShort(file):
	data = file.read(2)
	return unpack("h",data)[0]

def readFloat(file):
	data = file.read(4)
	return unpack("f",data)[0]

def readGUID(file):
    guid = uuid.UUID(bytes_le=file.read(16))
    return guid

def read_String_Element(file):
	string = ''
	string_size = readInt(file)
	#print(string_size)
	for i in range(string_size):
		char = readChar(file)
		string += char.decode('ascii')
	return string

def Read_Template_Element(file):
    #print("reading Template")
    guid = readGUID(file)
    #print(guid)
    array_elements_number = readInt(file)
    #print(array_elements_number)
    return guid, array_elements_number
	

def readBone_ani(file, armature, parents_only):
	guid , elements_num = Read_Template_Element(file)
	if str(guid).upper() == 'B84344DE-A1B6-4AA7-AFD6-22CA8A4B0CEE':
		file.read(1)

		#string  szName
		string_size = readInt(file)
		#print(string_size)

		szName = ''
		for i in range(string_size - 1):
			char = readChar(file)
			szName += char.decode('ascii')
		#print(szName)
		name = szName
		
		#dword	parent_Index
		file.read(2)
		parent_Index = readInt(file)
		#print(parent_Index)

		#'''
		
		if name not in armature.pose.bones and name.replace(' ','_') not in armature.pose.bones and name.replace('@','_') not in armature.pose.bones:
			return print(f"{name} not found")
		
		if name.replace(' ','_') in armature.pose.bones:
			name = name.replace(' ','_')
		
		if name.replace('@','_') in armature.pose.bones:
			name = name.replace('@','_')

		for bn in armature.pose.bones:
			if bn.name == name:
				bone = bn

		if parents_only and parent_Index != -1:
			armature.data.edit_bones[name].use_connect = False
			armature.data.edit_bones[name].parent = armature.data.edit_bones[parent_Index]

		if not parents_only:
			print(bone.name)
			#float	base_tm[16]
			file.read(2)
			base_tm_size = readInt(file)
			#print(base_tm_size)
			base_tm = []
			for i in range(base_tm_size):
				float = readFloat(file)
				base_tm.append(float)
			#print(base_tm)
			
			#dword	flag
			flag = readShort(file)
			#print(flag)
			
			#dword   pos_time_size;
			file.read(3)
			pos_time_size = int(readInt(file) / 8)
			#print(pos_time_size)

			
			#dword   pos_time_size
			file.read(1)
			pos_time_size = readInt(file)
			#print(pos_time_size)

			#dword   pos_time_array[pos_time_size]
			file.read(6)
			string_size = readInt(file)
			#print(string_size)
			file.read(string_size - 1)

			file.read(1)
			pos_time_array = []
			for i in range(pos_time_size):
				pos_time = readInt(file)
				pos_time_array.append(pos_time)
			#print(pos_time_array)

			#dword	pos_key_size
			file.read(1)
			pos_key_size = readInt(file)
			#print(pos_key_size)

			#float	pos_key_array[pos_key_size];
			file.read(6)
			string_size = readInt(file)
			#print(string_size)
			file.read(string_size - 1)

			file.read(1)
			pos_key_array = []
			for i in range(pos_time_size*3):
				pos_key = readFloat(file)
				pos_key_array.append(pos_key)
			#print(pos_key_array)
			




			#dword   rot_time_size;
			file.read(3)
			rot_time_size = int(readInt(file) / 8)
			#print(pos_time_size)

			
			#dword   rot_time_size
			#file.read(1)
			rot_time_size = readInt(file)
			#print(rot_time_size)

			
			#dword   rot_time_array[rot_time_size]
			#print(file.read(6))
			string_size = readInt(file)
			#print(string_size)
			file.read(string_size - 1)

			
			file.read(1)
			rot_time_array = []
			for i in range(rot_time_size):
				rot_time = readInt(file)
				rot_time_array.append(rot_time)
			#print(rot_time_array)
			
			#dword	rot_key_size
			file.read(1)
			rot_key_size = readInt(file)
			#print(rot_key_size)
			
			#float	rot_key_array[rot_key_size]
			file.read(6)
			string_size = readInt(file)
			#print(string_size)
			file.read(string_size - 1)
			
			file.read(1)
			rot_key_array = []
			for i in range(rot_time_size*4):
				rot_key = readFloat(file)
				rot_key_array.append(rot_key)
			#print(rot_key_array)



			#dword	child_size	
			file.read(1)
			child_size = readInt(file)
			#print(child_size)
			
			#dword	child_Index_array[child_size]
			file.read(2)
			child_Index_array = []
			for i in range(child_size):
				child_Index = readInt(file)
				child_Index_array.append(child_Index)
			#print(child_Index_array)

			bone.rotation_mode = 'QUATERNION'
			t, q, s = bone.matrix.decompose()

			for i, time in enumerate(pos_time_array):
				time = int(time / 100)

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

				bpy.context.scene.frame_start = int(pos_time_array[0] / 100)
				bpy.context.scene.frame_end = pos_time_array[len(pos_time_array) - 1] / 100


			file.read(20)
			#'''




def readDIFK(DIFK):
	with open(DIFK,'rb') as file:
		masterid = file.read(4)
		type = file.read(4)
			
		master_version = readInt(file)
		sub_version = readInt(file)
			
		nBlocks = readInt(file)
		
		print(masterid)
		print(type)
		#print(master_version)
		#print(sub_version)
		#print(nBlocks)
		
		seek = 20 + 108
		file.seek(seek)
			
		blockid = file.read(4)
		blocksize = readInt(file)
			
		#print(blockid)
		#print(blocksize)
		
		seek += 32
		file.seek(seek)
			
		MagicType = file.read(1)

		if bpy.context.active_object != None and bpy.context.active_object.type == 'ARMATURE':
			#print('starting')
			armature = bpy.context.active_object
			armature.ISDIFK = True
			new_armature = armature.copy()
			new_armature.data = new_armature.data.copy()
			bpy.context.collection.objects.link(new_armature)
		else:
			print("Please select the armature")
			return

		guid_main, elements_num_main = Read_Template_Element(file)
		if str(guid_main).upper() == 'E8F9296B-B9DD-4080-8BC7-6C69E0AA3FEB':
			bone_count = readInt(file)
			print(bone_count)

			f = file.read(8)
			#print(f)
			guid , elements_num = Read_Template_Element(file)
			if str(guid).upper() == '81B3C137-B2B8-40B0-A3AD-D149467F5932':
				size_field_name = read_String_Element(file)
				print(size_field_name)


			file.read(1)
			guid , elements_num = Read_Template_Element(file)
			if str(guid).upper() == '81B3C137-B2B8-40B0-A3AD-D149467F5932':
				file.read(1)
				channel_name_size = readInt(file)
				#print(channel_name_size)

				#string  channel_name
				channel_name = file.read(channel_name_size - 1)
				print(channel_name)
				
				#dword	channel_flag
				file.read(2)
				channel_flag = readInt(file)
				#print(channel_flag)

				#dword   channel_time_span
				file.read(1)
				channel_time_span = readInt(file)
				#print(channel_time_span)

				#dword   channel_frame_rate
				file.read(1)
				channel_frame_rate = readInt(file)
				#print(channel_frame_rate)
				bpy.context.scene.render.fps = channel_frame_rate
				
				#Template array bone_ani_array
				#dword bone_ani_size;
				file.read(1)
				bone_ani_size = readInt(file)
				print(bone_ani_size)

				file.read(2)
				guid , elements_num = Read_Template_Element(file)
				if str(guid).upper() == 'B84344DE-A1B6-4AA7-AFD6-22CA8A4B0CEE':
					#print(file.read(1))
					string_size = readInt(file)
					#print(string_size)
					file.read(string_size - 1)

				

				bpy.ops.object.mode_set(mode = 'EDIT')	
				file.read(2)
				for bone_ani in range(bone_ani_size):
					seek = file.tell()
					readBone_ani(file, armature, True)
					file.seek(seek)
					readBone_ani(file, new_armature, False)
				
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
				

