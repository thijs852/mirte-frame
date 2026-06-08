#!/usr/local/bin/python3
import sys

sys.path.append("/usr/lib/freecad-python3/lib/")
sys.path.append("/")
try:
    import FreeCAD
    import importDXF
    import Draft
    import Part
    import Mesh
except ValueError:
    print("FreeCAD library not found.")
    exit()
def makeRotatingPlacement(axis_origin, axis_dir, angle):
    import FreeCAD as App
    OZ = App.Vector(0,0,1)
    local_cs = App.Placement(axis_origin, App.Rotation(OZ, axis_dir))
    return local_cs.multiply(   App.Placement( App.Vector(), App.Rotation(angle,0,0) ).multiply( local_cs.inverse() )   )

def getFilePath(body, name, build_path, type):
    type_path = (build_path / type)
    if not type_path.exists():
       os.mkdir(type_path)
       
    attachment_path = "" 
    if name == "attachments":
        if not (type_path / "attachments").exists():
            os.mkdir((type_path / "attachments"))
        attachment_path = "attachments"

    label_postfix = ""
    if (body.Label != "Body"):
        label_postfix = "_" + body.Label
        label_postfix = label_postfix.replace("_body", "") # fix for layer bodies
    
    return str((type_path / attachment_path / (str(name) + label_postfix + "." + type)).resolve())
    
    
def exportSTL(body, name, build_path):
    pathOut = getFilePath(body, name, build_path, "stl")

    # Code as shown in FreeCAD console when generating stl file:
    __objs__ = []
    __objs__.append(body)

    if hasattr(Mesh, "exportOptions"):
        options = Mesh.exportOptions(pathOut)
        Mesh.export(__objs__, pathOut, options)
    else:
        Mesh.export(__objs__, pathOut)

    del __objs__
    
    
def exportSTEP(body, name, build_path):
    pathOut = getFilePath(body, name, build_path, "step")

    __objs__ = []
    __objs__.append(body)
    
    if hasattr(Part, "exportOptions"):
        options = Part.exportOptions(pathOut)
        Part.export(__objs__, pathOut, options)
    else:
        Part.export(__objs__, pathOut)

    del __objs__
    
    
def exportDXF(body, name, build_path):   
    # sv0 = Draft.make_shape2dview(body, FreeCAD.Vector(0, -1, 0))
    FreeCAD.getDocument(name).recompute()
    pathOut = getFilePath(body, name, build_path, "dxf")
    
    # Code as shown in FreeCAD console when generating dxf file:
    __objs__ = []
    __objs__.append(FreeCAD.getDocument(name).getObject(body.Name))
    spin = makeRotatingPlacement(FreeCAD.Vector(0,0,1),FreeCAD.Vector(1,0,0), -90)
    __objs__[0].Placement = spin.multiply(__objs__[0].Placement)
    FreeCAD.getDocument(name).recompute()
    if hasattr(importDXF, "exportOptions"):
        options = importDXF.exportOptions(pathOut)
        importDXF.export(__objs__, pathOut, options)
    else:
        d = importDXF.export(__objs__, pathOut)

    del __objs__
    
    
def renderFile(freecadFile):
    doc = FreeCAD.open(str(freecadFile))

    # Touch the parameters so they will be taken into account
    App.getDocument('parameters').getObject('Spreadsheet').importFile(str(dir_path / "scripts/params.csv"))
    #App.getDocument("parameters").Objects[0].touch()
    doc.recompute()

    bodies = list()
    for obj in doc.Objects:
        # Fix for motor clamp lock, the chamfer one is the final one
        if obj.isDerivedFrom("PartDesign::Body") or obj.isDerivedFrom("Part::Chamfer"):
            bodies.append(obj)
    
    # Find all ShapeString objects and change the font file to an absolute path
    for obj in doc.Objects:
        print(obj.Name, obj.TypeId, obj.isDerivedFrom("Part::Part2DObjectPython"))
        if obj.isDerivedFrom("Part::Part2DObjectPython"):
            font_path = obj.FontFile
            # get filename from font_path
            font_filename = Path(font_path).name
            abs_font_path = (freecadFile.parent / "../fonts" / font_filename).resolve() 
            # test if file exists
            if not abs_font_path.exists():
                print(f"Font file {abs_font_path} does not exist!")
                # print string to help debugging
                print(f"Original font path: {font_path}")
                print(f"Keys: {list(doc.getObject(obj.Name).PropertiesList)}")
            obj.FontFile = str(abs_font_path)
            print(f"Set font path for {obj.Name} to {obj.FontFile}")
    FreeCAD.getDocument(freecadFile.stem).recompute()
    for body in bodies:
        build_dir = (freecadFile.parent / "../build").resolve()
        if not build_dir.exists():
           os.mkdir(build_dir)
        exportDXF(body, freecadFile.stem, build_dir)
        exportSTL(body, freecadFile.stem, build_dir)
        exportSTEP(body, freecadFile.stem, build_dir)
    #FreeCAD.closeDocument(freecadFile.stem)


import os
import shutil
from pathlib import Path

dir_path =  Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute()
freecad_directory = (dir_path / "freecadFiles").resolve()

# clean build directory
if (dir_path / "build").exists():
    shutil.rmtree(dir_path / "build")

# render all freecad files
for filename in ["layer.FCStd"]: #os.listdir(freecad_directory):
    f = freecad_directory / filename
    if f.suffix == ".FCStd":
        print(f.stem)
        renderFile(f)