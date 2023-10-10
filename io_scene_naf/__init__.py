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

bl_info = {
	"name": "Rappelz NAF format",
	"author": "Glandu2/Peakz",
	"blender": (3, 0, 0),
	"version": (0, 3, 0),
	"location": "File > Import-Export",
	"description": "Export to a Rappelz NAF file",
	"category": "Import-Export"}

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty , BoolProperty
from . import export_naf
from . import import_naf
import imp


class ExportBTRFNAF(bpy.types.Operator, ExportHelper):
	bl_idname = "export_mesh.naf"
	bl_label = "Export NAF"
	bl_options = {'PRESET'}

	filepath : StringProperty(
			subtype='FILE_PATH',
			)

	filename_ext = ".naf"

	def execute(self, context):
		#options =[self.use_collection,self.use_selection]
		imp.reload(export_naf)
		#export_naf.write(self.filepath,*options)
		export_naf.write(self.filepath)
		return {'FINISHED'}

    


class ImportBTRFNAF(bpy.types.Operator, ImportHelper):
	bl_idname = "import_mesh.naf"
	bl_label = "Import NAF"
	bl_options = {'PRESET'}

	filepath : StringProperty(
			subtype='FILE_PATH',
			)

	filename_ext = ".naf"


	def execute(self, context):
		imp.reload(import_naf)
		import_naf.read(self.filepath)
		return {'FINISHED'}


def menu_func_export(self, context):
	self.layout.operator(ExportBTRFNAF.bl_idname, text="Rappelz NAF (.naf)")


def menu_func_import(self, context):
	self.layout.operator(ImportBTRFNAF.bl_idname, text="Rappelz NAF (.naf)")

classes = [
	ExportBTRFNAF,
	ImportBTRFNAF,
	]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


	bpy.types.Object.ISDIFK = BoolProperty(
        name="ISDIFK",
        description="Use DIFK time Export",
        default=False,
        subtype="NONE",
    )


def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

	del bpy.types.Object.ISDIFK

if __name__ == "__main__":
	register()
