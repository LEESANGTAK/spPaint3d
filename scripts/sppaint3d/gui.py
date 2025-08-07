# -----------------------------------------------------------------
#    SCRIPT            gui.py
#    AUTHOR            Sebastien Paviot
#                    spaviot @ gmail . com
#    DATE:            July,August 2009 - April,May 2010
#                        July 2021
#
#    DESCRIPTION:    Build Maya main tool and setup windows
#
#    VERSION:        2022.0
#
# -----------------------------------------------------------------

from __future__ import print_function

import sys
import random as rand

import maya.cmds as cmds

import sppaint3d.context as context

spPaint3dGuiID = "spPaint3d"
spPaint3dGuiID_Height = 740
spPaint3dSetupID = "spPaint3dSetup"
spPaint3dVersion = 2022.0

# debug to log some operation down to the script editor
sp3d_log = False

# optionVar name: (type, default value, corresponding class attribute)
# For now the class methods only check for 'iv' and 'fv' types while looping stuff
sp3dOptionVars = {
    "sp3dTransformRotate": ("iv", 1, "transformRotate"),
    "sp3dTransformScale": ("iv", 1, "transformScale"),
    "sp3dTransformScaleUniform": ("iv", 1, "transformScaleUniform"),
    "sp3dInstance": ("iv", 0, "instance"),
    "sp3dRandom": ("iv", 1, "random"),
    "sp3dAlign": ("iv", 1, "align"),
    "sp3dPaintFlux": ("iv", 1, "paintFlux"),
    "sp3dRampFX": ("fv", 0, "rampFX"),
    "sp3dRealTimeRampFX": ("iv", 0, "realTimeRampFX"),
    "sp3dPaintTimer": ("fv", 0.05, "paintTimer"),
    "sp3dPaintDistance": ("fv", 10, "paintDistance"),
    "sp3dPaintOffset": ("fv", 0, "upOffset"),
    "sp3dPlaceRotate": ("fv", 45, "placeRotate"),
    "sp3dContinuousTransform": ("iv", 0, "continuousTransform"),
    "sp3dJitter": ("iv", 0, "jitter"),
    "sp3dPreserveInConn": ("iv", 0, "preserveConn"),
    "sp3dSmoothNormal": ("iv", 1, "smoothNormal"),
    "sp3dSetupHierarchy": ("iv", 0, "hierarchy"),
    "sp3dGroup": ("fv", 0, "group"),
    "sp3dVersion": ("fv", spPaint3dVersion, "version")
}


class sp3dToolOption(object):
    """
    Class to store all tool related data
    """

    def __init__(self):
        """
        Build the object to store all variables.
        Initialize the default attributes and call the methods to update value from optionVars if necessary.
        """
        self.transformRotate = True
        self.transformScale = True
        self.transformScaleUniform = True
        self.instance = False
        self.random = True
        self.align = True
        self.paintFlux = True  # True=distance / False=timer
        self.jitter = False
        self.rampFX = 0  # 0=none, 1=rotate, 2=scale, 3=both
        self.realTimeRampFX = False
        self.paintTimer = 0.05
        self.paintDistance = 10
        self.placeRotate = 45
        self.continuousTransform = False  # Place mode only option, retransform cursor at every drag event
        self.upOffset = 0
        self.preserveConn = False
        self.smoothNormal = False  # false=decal mode, force pure normal from intersected triangle / true=smoothed normal per neighboring edges
        self.hierarchy = False  # False = no grouping of painted objects
        self.group = 0  # float value so it doesnt get converted into boolean when I batch read the Vars / 0=single group / 1=stroke group / 2=source group
        self.groupID = None  # used to track the group name where to sort the generated objects from the paint strokes
        self.version = spPaint3dVersion  # used to allow tracking of potentially erroneous obsolete optionVars

        if self.checkVars():
            # all optionVars seem to be in proper condition, will fetch the stored data and update the instance attributes
            self.loadVars()
        else:
            # seems there are issues with the optionVars and/or version mismatch
            cmds.confirmDialog(title='Script options alert',
                               message='It seems either the script is run for the first time or the version running is different than the saved data.\nAll options will be reseted to defaults!',
                               button=['Whatever'])

            # also deleting the main & setup windows prefs to avoid size issues across versions
            if cmds.windowPref(spPaint3dSetupID, exists=True):
                cmds.windowPref(spPaint3dSetupID, remove=True)
            if cmds.windowPref(spPaint3dGuiID, exists=True):
                cmds.windowPref(spPaint3dGuiID, remove=True)

            self.commitVars()

    def dumpVars(self):
        """
        print the value of all the tool option
        """
        print(self.__dict__)

    def checkVars(self):
        """
        Method to check if the stored optionVars contain valid data, if any.
        Returns False if any issue is detected.
        Returns True if all conditions are met and the method runs its course.
        """
        for name in sp3dOptionVars.keys():  # loop through all the optionVars from the global struct
            info = sp3dOptionVars[name]
            # iterating through all the currently valid optionVar names from the global struct, then fetching the stored value if it exists
            type, value, varname = info
            if not cmds.optionVar(exists=name):
                # name isnt' an existing optionVar
                return False
            if name == 'sp3dVersion' and cmds.optionVar(q=name) != value:
                # locally stored script version optionVar is obsolete
                return False

        # for loop exited before breaking, about to return True then
        return True

    def loadVars(self):
        """
        Will load the stored optionVars into self
        """
        for name in sp3dOptionVars.keys():  # loop through all the optionVars from the global struct
            info = sp3dOptionVars[name]
            # iterating through all the currently valid optionVar names from the global struct, then fetching the stored value if it exists
            type, value, varname = info
            if type == 'iv':
                # this is an int value to convert into bool
                self.__dict__[varname] = bool(cmds.optionVar(q=name))
            elif type == 'fv':
                self.__dict__[varname] = round(cmds.optionVar(q=name), 2)

        if sp3d_log:
            self.dumpVars()

    def resetVars(self):
        """
        Flush the values and restore default settings
        """
        for name in sp3dOptionVars.keys():  # loop through all the optionVars from the global struct
            info = sp3dOptionVars[name]
            # iterating through all the currently valid optionVar names from the global struct, then fetching the stored value if it exists
            type, value, varname = info
            if type == 'iv':
                # this is an int value to convert into bool
                cmds.optionVar(iv=(name, value))
            elif type == 'fv':
                # float value default
                cmds.optionVar(fv=(name, value))

        self.loadVars()

    def commitVars(self):
        """
        Method to store the data from instance attributes into optionVars.
        """
        for name in sp3dOptionVars.keys():  # force initialize optionVars to defaults
            info = sp3dOptionVars[name]
            type, value, varname = info
            if type == 'iv':
                # convert the bool attribute value into an int
                # print int(self.__dict__[varname])
                cmds.optionVar(iv=(name, int(self.__dict__[varname])))
            elif type == 'fv':
                # all other optionVar types
                cmds.optionVar(fv=(name, self.__dict__[varname]))
        if sp3d_log:
            self.dumpVars()

    def getGroupID(self):
        """
        Called during the onRelease event of a stroke. This method manages a consistent unique group name throughout the paint strokes
        """
        if not self.groupID:
            # group is not yet created
            self.groupID = cmds.group(empty=True, name='spPaint3dOutput')
        return self.groupID


class sp3dTransform(object):
    """
    contains values for the transform options
    """

    def __init__(self, rotate=((0, 0), (0, 0), (0, 0)), scale=((1, 1), (1, 1), (1, 1)), uJitter=(0, 0), vJitter=(0, 0)):
        """
        initialise attributes
        """
        self.rotate = rotate
        self.scale = scale
        self.uJitter = uJitter
        self.vJitter = vJitter

    def getRandomRotate(self):
        """
        return a (x,y,z) tuple with properly randomized value between the self.rotate bounds
        """
        x, y, z = self.rotate
        randxyz = (round(rand.uniform(x[0], x[1]), 3),
                   round(rand.uniform(y[0], y[1]), 3),
                   round(rand.uniform(z[0], z[1]), 3))
        return randxyz

    def getRandomScale(self, uniform):
        """
        return a (x,y,z) tuple with properly randomized value between the self.scale bounds
        """
        x, y, z = self.scale
        if uniform:
            randxyz = round(rand.uniform(x[0], x[1]), 3)
            return randxyz, randxyz, randxyz
        else:
            randxyz = (round(rand.uniform(x[0], x[1]), 3),
                       round(rand.uniform(y[0], y[1]), 3),
                       round(rand.uniform(z[0], z[1]), 3))
            return randxyz

    def getRandomJitter(self, space):
        """
        return a random value between the min and max from the corresponding space. space must be either 'uJitter' or 'vJitter'
        """
        min, max = self.__dict__[space]
        return round(rand.uniform(min, max), 3)


class sp3dObjectList(object):
    """
    store a dictionnary of objects, their DAG data and some other data
    dictionnary structure: { 'name as displayed in the list, also the name of the transform' : 'fullDAGPath', Activation bool (default True), Probability float (default 50%), Align Override (default UpAxis either be Y or Z)}
    """
    # define the list of authorized object type used when adding objects to lists
    authType = {
        'default': ('mesh',),
        'source': ('mesh', 'locator',),
        'target': ('mesh',)
    }

    def __init__(self, authorized='target', errorHandle=None):
        """
        initialize the default attributes.
        INPUT:     authorized = specify the type of authorized geometry for that list, fetched from the authType class attributes
                    valid values :    default / source / target (defined as class attributes)
        """
        # TODO
        self.obj = {}  # dictionnary of entries
        self.i = 0  # index values used if this is a source object list using sequential mode distribution
        self.auth = self.authType[authorized]  # used to sort 'valid' object when using the add method
        self.errorHandle = errorHandle

    def validateObjects(self):
        """
        Return True if all objects from the dictionnary really do/still exist in the scene (some monkeys delete objects while the script is running :))
        Return False once the method finds a missing object
        """
        if len(self.obj.keys()) == 0:
            return False  # list is empty
        for obj in self.obj.keys():
            data = self.obj[obj]
            if self.errorHandle:
                self.errorHandle.raiseError("INFO: validating object: %s", data[0])
            if not cmds.objExists(data[0]):
                return False
        if self.errorHandle:
            self.errorHandle.raiseError("INFO: Everything checks out")
        return True

    def hasDuplicate(self, compareobjlist):
        """
        Return True of there's any object from self found in the 'compareobjlist' dictionnary
        Return False if all objects are unique
        (In context: there can't be an object which is both a source object and a target surface)
        """
        for obj in compareobjlist.obj.keys():
            if self.alreadyExists(obj):
                return True
        return False

    def alreadyExists(self, obj):
        """
        check if obj already exists in the self.dictionnary
        """
        if obj in self.obj:
            return True
        else:
            return False

    def addObj(self, obj=None, dagPath=None, activation=True, proba=0.5, align='Up'):
        """
        append to the content of self.obj

        INPUT:    obj = object name (will become the entry key into the dictionnary)
                dagPath = full DAG path to that object
                activation = object is actually broadcasted into the poll of usable source objects, not used if the list is a target surface list
                proba = % probability presence when source objects are randomimzed, not used if the list is a target surface list
                align = axis override to compute the source object alignement on the target surface if align to surface option is On, not used if the list is a target surface list.
        RETURN: the name of the key if object was added properly, None otherwise
        """
        if self.alreadyExists(obj):
            # key already exists, return False and break
            return None, "Object already exists in the list and can't be added again"
        else:
            # Determine if obj is valid, or if has valid children
            objtype = cmds.objectType(obj)
            objchild = cmds.listRelatives(obj, children=True, shapes=True)  # get all the children shapes of the object

            if objtype in self.auth:
                # a shape was selected and is part of the authorized object types for this list type. will use the shape's name as the key
                self.obj[obj] = (getDAGPath(obj, True), activation, proba, align)
                return obj, True
            elif objtype == 'transform':
                # a transform was selected and checking now what lies underneath it
                # source valid object =
                # at least one of the children is a shape of auth type, that shape will be the key
                # if multiple shape of auth type, then the transform become the key
                # target valid object =
                # only 1 valid children of auth type
                if objchild is None:
                    # original object has no shapes among his 1st level children
                    return None, "Object doesn't seem to have any direct child of the proper type"
                elif len(objchild) == 1 and cmds.nodeType(objchild[0]) in self.auth:
                    # obj(transform) has only one child, and is of a proper type for the list, return objchild[0] as the key
                    obj = objchild[0]
                    # now checking the only children and might already have been added
                    if self.alreadyExists(obj):
                        return None, "Object already exists in the list and can't be added again"
                    else:
                        self.obj[obj] = (getDAGPath(obj, True), activation, proba, align)
                        return obj, True
                # elif(len(objchild)>1):
                # obj(transform) has multiple children and may be a group (or a mesh transform parenting other mesh)
                # check if at least one of the children is of the appropriate type
                else:
                    # hierarchy too complex. TODO
                    return None, "Does not compute (hierarchy too complex or whatever)"

            else:
                # doesn't fall in any valid category
                return None, "Object doesn't fit any valid category to be added to the list"

        # Never reach here

    def printObj(self):
        """
        print the content of the dictionnary
        mostly used for debug purpose
        """
        for obj in self.obj.keys():
            data = self.obj[obj]
            print("key: %s || DAG: %s" % (obj, data[0]))

    def delObj(self, obj=None):
        """
        delete obj from the self.obj dictionnary
        """
        # TODO: check if key really exists return False
        # TODO: delete the key:data and return True
        del self.obj[obj]

    def clrObj(self):
        """
        empty the dictionnary
        """
        self.obj = {}
        self.i = 0

    def getRandom(self, weighted=False):
        """
        will return a random entry dagMesh from the dictionnary.
        will return a weighted random entry using the proba attributes from each entry if the weighted boolean parameter is set
        will return None if the method was unsuccessful to retrieve the selected object (if object was deleted from the scene while the script was running for example)
        """
        # TODO: implement weight and boolean flag
        dkeys = list(self.obj.keys())
        dag = self.obj[dkeys[rand.randint(0, len(dkeys) - 1)]]
        return dag[0]

    def getNext(self):
        """
        will return the dagMesh of the next entry in the dictionnary. will increment the index by 1 (index will be calculated modulo the dictionnary length will polling for the next entry).
        will return None if the method was unsuccessful to retrieve the selected object (if object was deleted from the scene while the script was running for example)
        """
        # TODO: implement boolean flag
        dkeys = list(self.obj.keys())
        dkeys.sort()
        dag = self.obj[dkeys[self.i % len(dkeys)]]
        self.i += 1
        return dag[0]


class sp3derror(object):
    """
    class used to raise script error during the execution and display runtime info to the user in the bottom textfield of the main UI
    """

    def __init__(self, initerror, uifield):
        """
        initialise default attributes
        """
        self.error = initerror
        self.ui = uifield
        self.broadcastError()

    def broadcastError(self):
        """
        display the error in the proper field in the UI (self.uiInfoTextField)
        """
        cmds.textField(self.ui, edit=True, text=self.error)

    def raiseError(self, newerror):
        """
        update the error and call out to display it in the main UI
        """
        self.error = newerror
        self.broadcastError()


class spPaint3dWin(object):
    """
    Main UI window class definition
    """

    def __init__(self):
        # delete ui window if opened
        if cmds.window(spPaint3dGuiID, exists=True):
            cmds.deleteUI(spPaint3dGuiID)
        # removing delete prefs to prevent issues when window is spawned outside of display on mac?
        # if cmds.windowPref(spPaint3dGuiID, exists=True):
        #     cmds.windowPref(spPaint3dGuiID, remove=True)

        # delete option window if opened
        if cmds.window(spPaint3dSetupID, exists=True):
            cmds.deleteUI(spPaint3dSetupID)

        self.mayaVersion = getMayaVersion()

        self.uiWin = cmds.window(spPaint3dGuiID, title=("spPaint3d | " + str(spPaint3dVersion)), width=255,
                                 resizeToFitChildren=True, sizeable=True, titleBar=True, minimizeButton=False,
                                 maximizeButton=False, menuBar=False, menuBarVisible=False, toolbox=True)

        self.uiTopColumn = cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))

        # ----------------------
        # Top buttons
        # ----------------------
        self.uiTopForm = cmds.formLayout(numberOfDivisions=100)
        self.uiBtnHelp = cmds.button(label='Help', command=lambda *args: self.uiButtonCallback("uiBtnHelp", args))
        self.uiBtnOptions = cmds.button(label='Options',
                                        command=lambda *args: self.uiButtonCallback("uiBtnOptions", args))

        cmds.formLayout(self.uiTopForm, edit=True, attachControl=[(self.uiBtnOptions, 'left', 5, self.uiBtnHelp)])

        cmds.setParent(self.uiTopColumn)

        # ----------------------
        # Source Frame
        # ----------------------
        self.uiSourceFrame = cmds.frameLayout(label='Brush Geometry', collapsable=True,
                                              collapseCommand=lambda: self.resizeWindow('collapse', 109),
                                              expandCommand=lambda: self.resizeWindow('expand', 109), mh=5, mw=5)
        self.uiSourceForm = cmds.formLayout(numberOfDivisions=100, width=255)
        self.uiSourceList = cmds.textScrollList(numberOfRows=5, allowMultiSelection=True, width=215)
        self.uiSourceBtnAdd = cmds.symbolButton(w=60, h=18, ann='Add selected object(s) to the list',
                                                image='sp3dadd.xpm',
                                                command=lambda *args: self.uiListCallback("add", "uiSourceList"))
        self.uiSourceBtnRem = cmds.symbolButton(w=60, h=18, ann='Remove selected object(s) from the list',
                                                image='sp3drem.xpm',
                                                command=lambda *args: self.uiListCallback("rem", "uiSourceList"))
        self.uiSourceBtnClr = cmds.symbolButton(w=60, h=18, ann='Clear the list', image='sp3dclr.xpm',
                                                command=lambda *args: self.uiListCallback("clr", "uiSourceList"))

        cmds.formLayout(self.uiSourceForm, edit=True, attachForm=[(self.uiSourceList, 'top', 0)],
                        attachControl=[(self.uiSourceBtnAdd, 'top', 3, self.uiSourceList),
                                       (self.uiSourceBtnRem, 'left', 5, self.uiSourceBtnAdd),
                                       (self.uiSourceBtnRem, 'top', 3, self.uiSourceList),
                                       (self.uiSourceBtnClr, 'left', 5, self.uiSourceBtnRem),
                                       (self.uiSourceBtnClr, 'top', 3, self.uiSourceList)])

        cmds.setParent(self.uiTopColumn)

        # ----------------------
        # Transform Setup
        # ----------------------
        self.uiTransformFrame = cmds.frameLayout(label='Transform Setup', collapsable=True,
                                                 collapseCommand=lambda: self.resizeWindow('collapse', 177),
                                                 expandCommand=lambda: self.resizeWindow('expand', 177), mh=5, mw=5)
        self.uiTransformForm = cmds.formLayout(numberOfDivisions=100, width=255)
        self.uiTransformRotateCheck = cmds.checkBox(label='Rotate', ann='Activate the rotate transform while painting',
                                                    changeCommand=lambda *args: self.uiCheckBoxCallback(
                                                        "transformRotate", args))
        self.uiTransformRotateFieldX = cmds.floatFieldGrp(numberOfFields=2, label='Min', backgroundColor=(.81, .24, 0),
                                                          extraLabel='Max', cw4=(22, 50, 50, 30), precision=2,
                                                          ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                          changeCommand=lambda *args: self.uiTransformCallback())
        self.uiTransformRotateFieldY = cmds.floatFieldGrp(numberOfFields=2, label='', backgroundColor=(.41, .75, 0),
                                                          extraLabel='', cw4=(22, 50, 50, 30), precision=2,
                                                          ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                          changeCommand=lambda *args: self.uiTransformCallback())
        self.uiTransformRotateFieldZ = cmds.floatFieldGrp(numberOfFields=2, label='', backgroundColor=(.17, .4, .63),
                                                          extraLabel='', cw4=(22, 50, 50, 30), precision=2,
                                                          ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                          changeCommand=lambda *args: self.uiTransformCallback())
        self.uiTransformSeparator = cmds.separator(height=5, width=250, style='in')
        self.uiTransformScaleCheck = cmds.checkBox(label='Scale', ann='Activate the scale transform while painting',
                                                   changeCommand=lambda *args: self.uiCheckBoxCallback("transformScale",
                                                                                                       args))
        self.uiTransformScaleUniformCheck = cmds.checkBox(label='Uniform', ann='Force uniform scale while painting',
                                                          changeCommand=lambda *args: self.uiCheckBoxCallback(
                                                              "transformScaleUniform", args))
        self.uiTransformScaleFieldX = cmds.floatFieldGrp(numberOfFields=2, label='Min', backgroundColor=(.81, .24, 0),
                                                         extraLabel='Max', cw4=(22, 50, 50, 30), precision=2,
                                                         ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                         v1=1.0, v2=1.0,
                                                         changeCommand=lambda *args: self.uiTransformCallback())
        self.uiTransformScaleFieldY = cmds.floatFieldGrp(numberOfFields=2, label='', backgroundColor=(.41, .75, 0),
                                                         extraLabel='', cw4=(22, 50, 50, 30), precision=2,
                                                         ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                         v1=1.0, v2=1.0,
                                                         changeCommand=lambda *args: self.uiTransformCallback())
        self.uiTransformScaleFieldZ = cmds.floatFieldGrp(numberOfFields=2, label='', backgroundColor=(.17, .4, .63),
                                                         extraLabel='', cw4=(22, 50, 50, 30), precision=2,
                                                         ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                         v1=1.0, v2=1.0,
                                                         changeCommand=lambda *args: self.uiTransformCallback())

        cmds.formLayout(self.uiTransformForm, edit=True,
                        attachForm=[(self.uiTransformRotateCheck, 'top', 4), (self.uiTransformRotateFieldX, 'top', 0)],
                        attachControl=[(self.uiTransformRotateFieldX, 'left', 10, self.uiTransformRotateCheck),
                                       (self.uiTransformRotateFieldY, 'top', 5, self.uiTransformRotateFieldX),
                                       (self.uiTransformRotateFieldY, 'left', 10, self.uiTransformRotateCheck),
                                       (self.uiTransformRotateFieldZ, 'top', 5, self.uiTransformRotateFieldY),
                                       (self.uiTransformRotateFieldZ, 'left', 10, self.uiTransformRotateCheck),
                                       (self.uiTransformSeparator, 'top', 5, self.uiTransformRotateFieldZ),
                                       (self.uiTransformScaleCheck, 'top', 5, self.uiTransformSeparator),
                                       (self.uiTransformScaleUniformCheck, 'top', 5, self.uiTransformScaleCheck),
                                       (self.uiTransformScaleFieldX, 'top', 5, self.uiTransformSeparator),
                                       (self.uiTransformScaleFieldX, 'left', 15, self.uiTransformScaleCheck),
                                       (self.uiTransformScaleFieldY, 'top', 5, self.uiTransformScaleFieldX),
                                       (self.uiTransformScaleFieldY, 'left', 15, self.uiTransformScaleCheck),
                                       (self.uiTransformScaleFieldZ, 'top', 5, self.uiTransformScaleFieldY),
                                       (self.uiTransformScaleFieldZ, 'left', 15, self.uiTransformScaleCheck),
                                       ])

        cmds.setParent(self.uiTopColumn)
        self.transform = sp3dTransform()

        # ----------------------
        # Target Surface(s)
        # ----------------------
        self.uiTargetFrame = cmds.frameLayout(label='Target Surface(s)', collapsable=True,
                                              collapseCommand=lambda: self.resizeWindow('collapse', 109),
                                              expandCommand=lambda: self.resizeWindow('expand', 109), mh=5, mw=5)
        self.uiTargetForm = cmds.formLayout(numberOfDivisions=100, width=255)
        self.uiTargetList = cmds.textScrollList(numberOfRows=5, allowMultiSelection=True, width=215)
        self.uiTargetBtnAdd = cmds.symbolButton(w=60, h=18, ann='Add selected object(s) to the list',
                                                image='sp3dadd.xpm',
                                                command=lambda *args: self.uiListCallback("add", "uiTargetList"))
        self.uiTargetBtnRem = cmds.symbolButton(w=60, h=18, ann='Remove selected object(s) from the list',
                                                image='sp3drem.xpm',
                                                command=lambda *args: self.uiListCallback("rem", "uiTargetList"))
        self.uiTargetBtnClr = cmds.symbolButton(w=60, h=18, ann='Clear the list', image='sp3dclr.xpm',
                                                command=lambda *args: self.uiListCallback("clr", "uiTargetList"))

        cmds.formLayout(self.uiTargetForm, edit=True, attachForm=[(self.uiTargetList, 'top', 0)],
                        attachControl=[(self.uiTargetBtnAdd, 'top', 3, self.uiTargetList),
                                       (self.uiTargetBtnRem, 'left', 5, self.uiTargetBtnAdd),
                                       (self.uiTargetBtnRem, 'top', 3, self.uiTargetList),
                                       (self.uiTargetBtnClr, 'left', 5, self.uiTargetBtnRem),
                                       (self.uiTargetBtnClr, 'top', 3, self.uiTargetList)])

        cmds.setParent(self.uiTopColumn)

        # ----------------------
        # Paint Contexts
        # ----------------------
        self.uiPaintFrame = cmds.frameLayout(label='Paint', collapsable=True,
                                             collapseCommand=lambda: self.resizeWindow('collapse', 61),
                                             expandCommand=lambda: self.resizeWindow('expand', 61), mh=5, mw=5)
        self.uiPaintForm = cmds.formLayout(numberOfDivisions=100, width=255)
        self.uiPaintDupSCB = cmds.symbolCheckBox(w=52, h=18, ann='Duplicate: Instance or Copy', ofi='sp3dduplicate.xpm',
                                                 oni='sp3dinstance.xpm',
                                                 changeCommand=lambda *args: self.uiCheckBoxCallback("instance", args))
        self.uiPaintRandSCB = cmds.symbolCheckBox(w=52, h=18, ann='Object distribution: Random or Sequential',
                                                  ofi='sp3dsequence.xpm', oni='sp3drandom.xpm',
                                                  changeCommand=lambda *args: self.uiCheckBoxCallback("random", args))
        self.uiPaintAlignSCB = cmds.symbolCheckBox(w=100, h=18, ann='Align generated objects to the target surface',
                                                   ofi='sp3dalignoff.xpm', oni='sp3dalign.xpm',
                                                   changeCommand=lambda *args: self.uiCheckBoxCallback("align", args))
        self.uiPaintCtxBtn = cmds.symbolButton(w=105, h=28, ann='Paint', image='sp3dpaint.xpm',
                                               command=lambda *args: self.genericContextCallback("PaintCtx"))
        self.uiPlaceCtxBtn = cmds.symbolButton(w=105, h=28, ann='Place', image='sp3dplace.xpm',
                                               command=lambda *args: self.genericContextCallback("PlaceCtx"))

        cmds.formLayout(self.uiPaintForm, edit=True,
                        attachForm=[(self.uiPaintDupSCB, 'top', 0)],
                        attachControl=[(self.uiPaintRandSCB, 'left', 5, self.uiPaintDupSCB),
                                       (self.uiPaintAlignSCB, 'left', 5, self.uiPaintRandSCB),
                                       (self.uiPaintCtxBtn, 'top', 5, self.uiPaintDupSCB),
                                       (self.uiPlaceCtxBtn, 'top', 5, self.uiPaintDupSCB),
                                       (self.uiPlaceCtxBtn, 'left', 5, self.uiPaintCtxBtn)])

        cmds.setParent(self.uiTopColumn)

        # ----------------------
        # Paint Metrics
        # ----------------------
        self.uiPaintMetricsFrame = cmds.frameLayout(label='Paint Options', collapsable=True,
                                                    collapseCommand=lambda: self.resizeWindow('collapse', 129),
                                                    expandCommand=lambda: self.resizeWindow('expand', 129), mh=5, mw=5)
        self.uiPaintMetricsForm = cmds.formLayout(numberOfDivisions=100, width=255)
        self.uiPaintTimer = cmds.floatSliderGrp(label='Sensibility', field=1, minValue=0.0, maxValue=0.2,
                                                fieldMaxValue=1.0, precision=2, vis=False, w=250, cw=[(1, 55), (2, 35)],
                                                changeCommand=lambda *args: self.uiFluxCallback("paintTimer", args),
                                                extraLabel='(interval in second)')
        self.uiPaintDistance = cmds.floatFieldGrp(label='Distance threshold', precision=2, vis=False, w=250,
                                                  cw=[(1, 100), (2, 50)],
                                                  changeCommand=lambda *args: self.uiFluxCallback("paintDistance",
                                                                                                  args),
                                                  extraLabel='')
        self.uiPaintMetricsSep1 = cmds.separator(w=250)
        self.uiUpOffset = cmds.floatFieldGrp(label='Up Offset', precision=2, vis=True, w=100, cw=[(1, 54), (2, 40)],
                                             changeCommand=lambda *args: self.uiPaintOffsetCallback("upOffset", args))
        self.uiPaintMetricsRampMenu = cmds.optionMenu(l='Ramp FX',
                                                      changeCommand=lambda *args: self.uiRampMenuCallback("rampMenu",
                                                                                                          args))
        cmds.menuItem(label=' ')
        cmds.menuItem(label='rotate')
        cmds.menuItem(label='scale')
        cmds.menuItem(label='both')
        self.uiPaintMetricsSep2 = cmds.separator(w=250)

        self.uiJitterCheck = cmds.checkBox(label='Jitter', ann='Activate jitter transform along U & V while painting',
                                           changeCommand=lambda *args: self.uiCheckBoxCallback("jitter", args))
        self.uiJitterFieldU = cmds.floatFieldGrp(numberOfFields=2, label='Min U', backgroundColor=(.895, .735, 0.176),
                                                 extraLabel='Max', cw4=(32, 50, 50, 30), precision=2,
                                                 ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                 changeCommand=lambda *args: self.uiTransformCallback())
        self.uiJitterFieldV = cmds.floatFieldGrp(numberOfFields=2, label='Min V', backgroundColor=(.692, .323, 0.851),
                                                 extraLabel='', cw4=(32, 50, 50, 30), precision=2,
                                                 ct4=('right', 'both', 'both', 'right'), co4=(2, 2, 2, 8),
                                                 changeCommand=lambda *args: self.uiTransformCallback())

        cmds.formLayout(self.uiPaintMetricsForm, edit=True,
                        attachForm=[
                            (self.uiPaintTimer, 'top', 0),
                            (self.uiPaintDistance, 'top', 0),
                        ],
                        attachControl=[
                            (self.uiPaintMetricsSep1, 'top', 5, self.uiPaintTimer),
                            (self.uiPaintMetricsSep1, 'top', 5, self.uiPaintDistance),
                            (self.uiUpOffset, 'top', 5, self.uiPaintMetricsSep1),
                            (self.uiPaintMetricsRampMenu, 'top', 6, self.uiPaintMetricsSep1),
                            (self.uiPaintMetricsRampMenu, 'left', 10, self.uiUpOffset),
                            (self.uiPaintMetricsSep2, 'top', 5, self.uiUpOffset),
                        ])

        cmds.formLayout(self.uiPaintMetricsForm, edit=True,
                        attachControl=[(self.uiJitterCheck, 'top', 5, self.uiPaintMetricsSep2),
                                       (self.uiJitterFieldU, 'left', 5, self.uiJitterCheck),
                                       (self.uiJitterFieldU, 'top', 5, self.uiPaintMetricsSep2),
                                       (self.uiJitterFieldV, 'top', 5, self.uiJitterFieldU),
                                       (self.uiJitterFieldV, 'left', 5, self.uiJitterCheck)])

        cmds.setParent(self.uiTopColumn)

        # ----------------------
        # Footer
        # ----------------------
        self.uiInfoFrame = cmds.frameLayout(labelVisible=False)
        self.uiInfoTextField = cmds.textField(editable=False)
        self.errorHandle = sp3derror((spPaint3dGuiID + ' ' + str(spPaint3dVersion) + ' | Sebastien Paviot - 2009-2022'),
                                     self.uiInfoTextField)

        # ----------------------
        # Update UI controls
        # ----------------------
        self.uiValues = sp3dToolOption()
        self.updateUIControls(self.uiValues)

        # ----------------------
        # Source & Target object lists
        # ----------------------
        self.sourceList = sp3dObjectList('source')
        self.targetList = sp3dObjectList('target')

        # ----------------------
        # Context tracking
        # ----------------------
        self.ctx = None

        self.uiUpdatePaintDistanceUnit()
        cmds.showWindow(self.uiWin)
        self.resizeWindow('winui', spPaint3dGuiID_Height)  # force a resize to prevent some weird UI issue on mac
        if sp3d_log:
            self.debugFrameSize()  # display actual corrected ui frame sizes

    def uiUpdatePaintDistanceUnit(self):
        unit = cmds.currentUnit(query=True, linear=True)
        cmds.floatFieldGrp(self.uiPaintDistance, edit=True, extraLabel=unit)

    def uiTransformCallback(self, *args):
        """
        rebuild the transform combo tuple and feed the class when changed in the UI
        """
        rotate = ((cmds.floatFieldGrp(self.uiTransformRotateFieldX, q=True, v1=True),
                   cmds.floatFieldGrp(self.uiTransformRotateFieldX, q=True, v2=True)), (
                      cmds.floatFieldGrp(self.uiTransformRotateFieldY, q=True, v1=True),
                      cmds.floatFieldGrp(self.uiTransformRotateFieldY, q=True, v2=True)), (
                      cmds.floatFieldGrp(self.uiTransformRotateFieldZ, q=True, v1=True),
                      cmds.floatFieldGrp(self.uiTransformRotateFieldZ, q=True, v2=True)))
        scale = ((cmds.floatFieldGrp(self.uiTransformScaleFieldX, q=True, v1=True),
                  cmds.floatFieldGrp(self.uiTransformScaleFieldX, q=True, v2=True)), (
                     cmds.floatFieldGrp(self.uiTransformScaleFieldY, q=True, v1=True),
                     cmds.floatFieldGrp(self.uiTransformScaleFieldY, q=True, v2=True)), (
                     cmds.floatFieldGrp(self.uiTransformScaleFieldZ, q=True, v1=True),
                     cmds.floatFieldGrp(self.uiTransformScaleFieldZ, q=True, v2=True)))
        uJitter = (cmds.floatFieldGrp(self.uiJitterFieldU, q=True, v1=True),
                   cmds.floatFieldGrp(self.uiJitterFieldU, q=True, v2=True))
        vJitter = (cmds.floatFieldGrp(self.uiJitterFieldV, q=True, v1=True),
                   cmds.floatFieldGrp(self.uiJitterFieldV, q=True, v2=True))
        self.transform = sp3dTransform(rotate, scale, uJitter, vJitter)
        self.updateCtx()

    def uiRampMenuCallback(self, *args):
        """
        ramp effect menu stuff
        """
        if args[1][0] == 'rotate':
            self.uiValues.rampFX = 1
        elif args[1][0] == 'scale':
            self.uiValues.rampFX = 2
        elif args[1][0] == 'both':
            self.uiValues.rampFX = 3
        else:
            self.uiValues.rampFX = 0
        self.uiValues.commitVars()
        self.updateCtx()

    def uiTransformReset(self):
        """
        reset transform values and update UI
        """
        self.transform = sp3dTransform()
        cmds.floatFieldGrp(self.uiTransformRotateFieldX, e=True, v1=0, v2=0)
        cmds.floatFieldGrp(self.uiTransformRotateFieldY, e=True, v1=0, v2=0)
        cmds.floatFieldGrp(self.uiTransformRotateFieldZ, e=True, v1=0, v2=0)
        cmds.floatFieldGrp(self.uiTransformScaleFieldX, e=True, v1=1, v2=1)
        cmds.floatFieldGrp(self.uiTransformScaleFieldY, e=True, v1=1, v2=1)
        cmds.floatFieldGrp(self.uiTransformScaleFieldZ, e=True, v1=1, v2=1)

        cmds.floatFieldGrp(self.uiJitterFieldU, e=True, v1=0, v2=0)
        cmds.floatFieldGrp(self.uiJitterFieldV, e=True, v1=0, v2=0)

    def uiFluxCallback(self, *args):
        """
        Callback for timer slider and distance float field change
        INPUT: [variable name, (value to update,)]
        """
        self.uiValues.__dict__[args[0]] = float(args[1][0])
        self.uiValues.commitVars()
        self.uiUpdatePaintDistanceUnit()
        self.updateCtx()

    def uiPaintOffsetCallback(self, *args):
        """
        Callback for paint Offset field change
        INPUT: [variable name, (value to update,)]
        """
        self.uiValues.__dict__[args[0]] = float(args[1][0])
        self.uiValues.commitVars()
        self.updateCtx()

    def uiButtonCallback(self, *args):
        """
        Callback for top buttons
        INPUT: [variable name]
        """
        button = args[0]
        if button == 'uiBtnHelp':
            cmds.confirmDialog(title=spPaint3dGuiID + ' ' + str(spPaint3dVersion) + ' Help',
                               message='Please refer to the README file for detailed help on how to use the script.\n Or use the Homepage button in the Options.',
                               button='Whatever')
        elif button == 'uiBtnOptions':
            self.setupWin(self.uiValues)

    def uiCheckBoxCallback(self, *args):
        """
        Callback for checkbox and symbolCheckbox
        INPUT: [variable name, (string value for bool state,)]
        """
        if sp3d_log:
            print('input from UI: %s of type %s' % (args, args[1][0].__class__))
        self.uiValues.__dict__[args[0]] = getBoolFromMayaControl(args[1][0], self.mayaVersion)
        self.uiValues.commitVars()
        self.updateCtx()

    def updateUIControls(self, ui):
        """
        Will update the self ui controls with the values stores in the passed instance object
        """
        cmds.checkBox(self.uiTransformRotateCheck, edit=True, value=ui.transformRotate)
        cmds.checkBox(self.uiTransformScaleCheck, edit=True, value=ui.transformScale)
        cmds.checkBox(self.uiTransformScaleUniformCheck, edit=True, value=ui.transformScaleUniform)
        cmds.checkBox(self.uiJitterCheck, edit=True, value=ui.jitter)
        cmds.symbolCheckBox(self.uiPaintDupSCB, edit=True, value=ui.instance)
        cmds.symbolCheckBox(self.uiPaintRandSCB, edit=True, value=ui.random)
        cmds.symbolCheckBox(self.uiPaintAlignSCB, edit=True, value=ui.align)

        # toggling the proper paint flux control
        cmds.floatSliderGrp(self.uiPaintTimer, edit=True, visible=(not ui.paintFlux), value=ui.paintTimer)
        cmds.floatFieldGrp(self.uiPaintDistance, edit=True, visible=ui.paintFlux, v1=ui.paintDistance)

        visible_control = self.uiPaintDistance if ui.paintFlux else self.uiPaintTimer
        cmds.formLayout(self.uiPaintMetricsForm, edit=True,
                        attachForm=[(visible_control, 'top', 0), ],
                        attachControl=[(self.uiPaintMetricsSep1, 'top', 5, visible_control), ])

        # feeding place rotate threshold
        cmds.floatFieldGrp(self.uiUpOffset, edit=True, visible=True, v1=ui.upOffset)

        if ui.rampFX == 1:
            cmds.optionMenu(self.uiPaintMetricsRampMenu, edit=True, value='rotate')
        elif ui.rampFX == 2:
            cmds.optionMenu(self.uiPaintMetricsRampMenu, edit=True, value='scale')
        elif ui.rampFX == 3:
            cmds.optionMenu(self.uiPaintMetricsRampMenu, edit=True, value='both')
        else:
            cmds.optionMenu(self.uiPaintMetricsRampMenu, edit=True, value=' ')

    def debugFrameSize(self):
        """
        Will query and print the actual size of the frame to collapse. Will already remove 21 from the total height, so ready to use with the resizeWindow onCollapse command
        """
        print("sourceFrame: %i" % (cmds.frameLayout(self.uiSourceFrame, query=True, height=True) - 21))
        print("transformFrame: %i" % (cmds.frameLayout(self.uiTransformFrame, query=True, height=True) - 21))
        print("targetFrame: %i" % (cmds.frameLayout(self.uiTargetFrame, query=True, height=True) - 21))
        print("paintFrame: %i" % (cmds.frameLayout(self.uiPaintFrame, query=True, height=True) - 21))
        print("paintMetricFrame: %i" % (cmds.frameLayout(self.uiPaintMetricsFrame, query=True, height=True) - 21))

    def resizeWindow(self, direction, offset):
        """
        Will adjust the size of the window, used when collapsing/expanding frames
        """
        if cmds.window(spPaint3dGuiID, exists=True):
            currentSize = cmds.window(self.uiWin, query=True, height=True)

            if direction == 'collapse':
                currentSize -= offset
            elif direction == 'expand':
                # the windows should auto resize to fit all its children
                return
            elif direction == 'winui':
                currentSize = offset

            if currentSize > 0:
                cmds.window(self.uiWin, edit=True, height=currentSize)

        # self.debugFrameSize()

    def updateCtx(self):
        """
        method to check if there's any running context to update
        """
        if self.ctx:
            # there's a context object that can be updated
            self.ctx.runtimeUpdate(self.uiValues, self.transform, self.sourceList, self.targetList)

    def uiListCallback(self, *args):
        """
        textScrollList callback to manage the addition/removal/reset of the source & target object lists
        """
        # print "listStuff: " + str(args)
        mode = args[0]
        textlist = args[1]
        if textlist == 'uiSourceList':
            objlist = 'sourceList'
        else:
            objlist = 'targetList'

        if mode == 'add':
            # ADD
            objselected = cmds.ls(selection=True)
            for obj in objselected:
                addresult, addcomment = self.__dict__[objlist].addObj(obj)
                if addresult == None:
                    # an exception occured, printing debut info
                    self.errorHandle.raiseError(addcomment)
                else:
                    # an object was added to the dict, to be added to the UI list
                    if cmds.objExists(addresult):
                        # making sure the object does exist
                        cmds.textScrollList(self.__dict__[textlist], edit=True, append=addresult)
                        # print ('added succesfully:', addresult)

        elif mode == 'clr':
            # CLEAR
            cmds.textScrollList(self.__dict__[textlist], edit=True, removeAll=True)
            self.__dict__[objlist].clrObj()

        elif mode == 'rem':
            # REMOVE
            remlist = cmds.textScrollList(self.__dict__[textlist], query=True, selectItem=True)
            if remlist:
                # list is not empty
                for remobj in remlist:
                    # iterate through all the selected obj to remove
                    self.__dict__[objlist].delObj(remobj)
                    cmds.textScrollList(self.__dict__[textlist], edit=True, removeItem=remobj)

        # self.__dict__[objlist].printObj()
        self.updateCtx()

    def genericContextCallback(self, *args):
        """
        Handle the paint/place context button callbacks
        """
        # print "genericCallback called: " + str(args)

        # delete the setup option UI if it's opened
        if cmds.window(spPaint3dSetupID, exists=True):
            cmds.deleteUI(spPaint3dSetupID)

        # validate the objects from both lists and raise an error if necessary
        sourcevalid = self.sourceList.validateObjects()
        targetvalid = self.targetList.validateObjects()
        duplicateerror = self.sourceList.hasDuplicate(self.targetList)

        self.uiUpdatePaintDistanceUnit()

        if not sourcevalid:
            self.errorHandle.raiseError("Source list is empty or object(s) have been deleted. FIX!")
        elif not targetvalid:
            self.errorHandle.raiseError("Target list is empty or object(s) have been deleted. FIX!")
        elif duplicateerror:
            self.errorHandle.raiseError("Object(s) can't be in both lists, FIX!")
        else:
            # if we reach here, then there seem to be no errors caught
            # call the appropriate context and set self attributes
            if args[0] == 'PaintCtx':
                # creating (or overwritring with) a paint context
                self.errorHandle.raiseError("Engage!! Maximum Paint...")
                self.ctx = context.paintContext(self.uiValues, self.transform, self.sourceList,
                                                self.targetList)
                self.ctx.runContext()
            elif args[0] == 'PlaceCtx':
                # creating (or overwritring with) a place context
                self.errorHandle.raiseError("Engage!! Maximum Place...")
                self.ctx = context.placeContext(self.uiValues, self.transform, self.sourceList,
                                                self.targetList)
                self.ctx.runContext()

    def setupWin(self, uiOptions):
        """
        Create setup UI
        """
        if cmds.window(spPaint3dSetupID, exists=True):
            cmds.deleteUI(spPaint3dSetupID)

        self.uiSetupWin = cmds.window(spPaint3dSetupID, title=("spPaint3dSetup | " + str(spPaint3dVersion)), width=250,
                                      height=450, resizeToFitChildren=True, sizeable=True, titleBar=True,
                                      minimizeButton=False, maximizeButton=False, menuBar=False, menuBarVisible=False,
                                      toolbox=True)

        # ----------------------
        # Top buttons
        # ----------------------
        self.uiSetupTopColumn = cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
        self.uiSetupTopForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupBtnHelp = cmds.button(label='Help',
                                          command=lambda *args: self.setupButtonCallback('uiSetupBtnHelp', args))
        self.uiSetupBtnHomepage = cmds.button(label='Homepage',
                                              command=lambda *args: self.setupButtonCallback('uiSetupBtnHomepage',
                                                                                             args))
        self.uiSetupBtnReset = cmds.button(label='Reset',
                                           command=lambda *args: self.setupButtonCallback('uiSetupBtnReset', args))

        cmds.formLayout(self.uiSetupTopForm, edit=True,
                        attachControl=[(self.uiSetupBtnHomepage, 'left', 5, self.uiSetupBtnHelp),
                                       (self.uiSetupBtnReset, 'left', 5, self.uiSetupBtnHomepage)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Duplicate Options
        # ----------------------
        self.uiSetupDuplicateFrame = cmds.frameLayout(label='Duplicate Options', marginHeight=5, marginWidth=20)
        self.uiSetupDuplicateForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupChkInputConn = cmds.checkBoxGrp(label='Preserve input connections',
                                                    changeCommand=lambda *args: self.setupCallback(
                                                        'uiSetupChkInputConn', args), numberOfCheckBoxes=1, width=170)

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Surface Normals
        # ----------------------
        self.uiSetupNormalFrame = cmds.frameLayout(label='Surface Normals', marginHeight=5, marginWidth=20)
        self.uiSetupNormalForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupNormalCol = cmds.radioCollection()
        self.uiSetupNormalSmooth = cmds.radioButton(label='Geometry normal', align='right',
                                                    onCommand=lambda *args: self.setupCallback('uiSetupNormalCol',
                                                                                               True))
        self.uiSetupNormalHard = cmds.radioButton(label='Force hard normal', align='right',
                                                  onCommand=lambda *args: self.setupCallback('uiSetupNormalCol', False))

        cmds.formLayout(self.uiSetupNormalForm, edit=True,
                        attachControl=[(self.uiSetupNormalHard, 'top', 5, self.uiSetupNormalSmooth)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Flux control
        # ----------------------
        self.uiSetupFluxFrame = cmds.frameLayout(label='Flux Control', marginHeight=5, marginWidth=20)
        self.uiSetupFluxForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupFluxCol = cmds.radioCollection()
        self.uiSetupFluxTimer = cmds.radioButton(label='Timer', align='right',
                                                 onCommand=lambda *args: self.setupCallback('uiSetupFluxCol', False))
        self.uiSetupFluxDistance = cmds.radioButton(label='Distance threshold', align='right',
                                                    onCommand=lambda *args: self.setupCallback('uiSetupFluxCol', True))

        cmds.formLayout(self.uiSetupFluxForm, edit=True,
                        attachControl=[(self.uiSetupFluxDistance, 'top', 5, self.uiSetupFluxTimer)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Hierarchy
        # ----------------------
        self.uiSetupHierarchyFrame = cmds.frameLayout(label='Hierarchy Management', marginHeight=5, marginWidth=20)
        self.uiSetupHierarchyForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupHierarchyActive = cmds.checkBoxGrp(label='Activate objects grouping',
                                                       changeCommand=lambda *args: self.setupCallback(
                                                           'uiSetupHierarchyActive', args), numberOfCheckBoxes=1)
        self.uiSetupHierarchyCol = cmds.radioCollection()
        self.uiSetupHierarchySession = cmds.radioButton(label='Single paint session group', align='right',
                                                        onCommand=lambda *args: self.setupCallback(
                                                            'uiSetupHierarchySession', args))
        self.uiSetupHierarchyStroke = cmds.radioButton(label='Stroke sorted group(s)', align='right',
                                                       onCommand=lambda *args: self.setupCallback(
                                                           'uiSetupHierarchyStroke', args))
        self.uiSetupHierarchySource = cmds.radioButton(label='Source sorted group(s)', align='right',
                                                       onCommand=lambda *args: self.setupCallback(
                                                           'uiSetupHierarchySource', args))

        cmds.formLayout(self.uiSetupHierarchyForm, edit=True,
                        attachControl=[(self.uiSetupHierarchySession, 'top', 5, self.uiSetupHierarchyActive),
                                       (self.uiSetupHierarchyStroke, 'top', 5, self.uiSetupHierarchySession),
                                       (self.uiSetupHierarchySource, 'top', 5, self.uiSetupHierarchyStroke)])
        cmds.formLayout(self.uiSetupHierarchyForm, edit=True, attachForm=[(self.uiSetupHierarchySession, 'left', 25),
                                                                          (self.uiSetupHierarchyStroke, 'left', 25),
                                                                          (self.uiSetupHierarchySource, 'left', 25)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Place Options
        # ----------------------
        self.uiSetupPaintOptionsFrame = cmds.frameLayout(label='Place Options', marginHeight=5, marginWidth=20)
        self.uiSetupPaintOptionsForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupPlaceRotate = cmds.floatFieldGrp(label='Place Mode rotate increment', precision=2, vis=True, w=250,
                                                     cw=[(1, 145), (2, 50)],
                                                     changeCommand=lambda *args: self.uiSetupPlaceRotateCallback(
                                                         "placeRotate", args))
        self.uiSetupContinuousTransform = cmds.checkBoxGrp(label='Continuous transform',
                                                           changeCommand=lambda *args: self.setupCallback(
                                                               'uiSetupContinuousTransform', args),
                                                           numberOfCheckBoxes=1)

        cmds.formLayout(self.uiSetupPaintOptionsForm, edit=True, attachForm=[(self.uiSetupPlaceRotate, 'top', 0)],
                        attachControl=[(self.uiSetupContinuousTransform, 'top', 5, self.uiSetupPlaceRotate)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # Dev feature
        # ----------------------
        self.uiSetupDevFrame = cmds.frameLayout(label='Development Feature', marginHeight=5, marginWidth=20)
        self.uiSetupDevForm = cmds.formLayout(numberOfDivisions=100)
        self.uiSetupRealTimeRampFX = cmds.checkBoxGrp(label='Realtime RampFX',
                                                      changeCommand=lambda *args: self.setupCallback(
                                                          'uiSetupRealTimeRampFX', args), numberOfCheckBoxes=1)

        cmds.formLayout(self.uiSetupDevForm, edit=True,
                        attachForm=[(self.uiSetupRealTimeRampFX, 'top', 0), (self.uiSetupRealTimeRampFX, 'left', 0)])

        cmds.setParent(self.uiSetupTopColumn)

        # ----------------------
        # 
        # ----------------------

        self.updateUISetupControls(uiOptions)
        cmds.showWindow(self.uiSetupWin)

    def updateUISetupControls(self, ui):
        """
        Will update the self ui controls with the values stores in the passed instance object
        """
        if sp3d_log:
            print(ui.__dict__)
        cmds.checkBoxGrp(self.uiSetupChkInputConn, edit=True, value1=ui.preserveConn)
        cmds.checkBoxGrp(self.uiSetupRealTimeRampFX, edit=True, value1=ui.realTimeRampFX)
        cmds.radioButton(self.uiSetupNormalSmooth, edit=True, select=ui.smoothNormal)
        cmds.radioButton(self.uiSetupNormalHard, edit=True, select=(not ui.smoothNormal))
        cmds.radioButton(self.uiSetupFluxTimer, edit=True, select=(not ui.paintFlux))
        cmds.radioButton(self.uiSetupFluxDistance, edit=True, select=ui.paintFlux)

        cmds.floatFieldGrp(self.uiSetupPlaceRotate, edit=True, visible=True, v1=ui.placeRotate)
        cmds.checkBoxGrp(self.uiSetupContinuousTransform, edit=True, value1=ui.continuousTransform)

        # toggling the proper hierarchy grouping options
        cmds.checkBoxGrp(self.uiSetupHierarchyActive, edit=True, value1=ui.hierarchy)
        if sp3d_log:
            print("ui.hierarchy %s" % ui.hierarchy)
        if ui.hierarchy:
            # toggling radio button enabled
            if sp3d_log:
                print("toggling grouping option ON")
            cmds.radioButton(self.uiSetupHierarchySession, edit=True, enable=True)
            cmds.radioButton(self.uiSetupHierarchyStroke, edit=True, enable=True)
            cmds.radioButton(self.uiSetupHierarchySource, edit=True, enable=True)
        else:
            # toggling radio button disable
            if sp3d_log:
                print("toggling grouping option OFF")
            cmds.radioButton(self.uiSetupHierarchySession, edit=True, enable=False)
            cmds.radioButton(self.uiSetupHierarchyStroke, edit=True, enable=False)
            cmds.radioButton(self.uiSetupHierarchySource, edit=True, enable=False)

        if ui.group == 0.0:
            cmds.radioButton(self.uiSetupHierarchySession, edit=True, select=True)
        elif ui.group == 1.0:
            cmds.radioButton(self.uiSetupHierarchyStroke, edit=True, select=True)
        elif ui.group == 2.0:
            cmds.radioButton(self.uiSetupHierarchySource, edit=True, select=True)

    def resetOptions(self):
        """
        Will reset to defaults the options
        """
        # TODO: loop/reset the option
        # TODO: update setup window UI
        # TODO: callback main UI window for update
        # TODO: callback to context if active with new options
        self.uiValues.resetVars()
        self.updateUISetupControls(self.uiValues)
        self.updateUIControls(self.uiValues)
        self.uiTransformReset()

        # deleting windowprefs and forcing resize
        if cmds.windowPref(spPaint3dSetupID, exists=True):
            cmds.windowPref(spPaint3dSetupID, remove=True)
        if cmds.windowPref(spPaint3dGuiID, exists=True):
            cmds.windowPref(spPaint3dGuiID, remove=True)

        if cmds.window(spPaint3dGuiID, exists=True):
            # forcing all frame to uncollapse if any
            cmds.frameLayout(self.uiSourceFrame, edit=True, collapse=False)
            cmds.frameLayout(self.uiTransformFrame, edit=True, collapse=False)
            cmds.frameLayout(self.uiTargetFrame, edit=True, collapse=False)
            cmds.frameLayout(self.uiPaintFrame, edit=True, collapse=False)
            cmds.frameLayout(self.uiPaintMetricsFrame, edit=True, collapse=False)
            self.resizeWindow('winui', spPaint3dGuiID_Height)  # force a resize to prevent some weird UI issue on mac

    def setupButtonCallback(self, *args):
        """
        Manage top buttons commands
        """
        button = args[0]
        if button == 'uiSetupBtnHelp':
            cmds.confirmDialog(title=spPaint3dGuiID + ' ' + str(spPaint3dVersion) + ' Help',
                               message='Please refer to the README file for detailed help on how to use the script.\n Or use the Homepage button right there.',
                               button='Whatever')
        elif button == 'uiSetupBtnHomepage':
            cmds.showHelp(
                'http://www.creativecrash.com/maya/downloads/scripts-plugins/utility-external/misc/c/sppaint3d',
                absolute=True)
        elif button == 'uiSetupBtnReset':
            self.resetOptions()

    def uiSetupPlaceRotateCallback(self, *args):
        """
        Callback for place rotate field change
        INPUT: [variable name, (value to update,)]
        """
        self.uiValues.__dict__[args[0]] = float(args[1][0])
        self.uiValues.commitVars()
        self.updateCtx()

    def setupCallback(self, *args):
        """
        Manage checkbox and radio buttons
        uiNormalCol
        uiFluxCol
        uiSetupHierarchyActive
        """
        radiocol = args[0]
        if sp3d_log:
            print('setupCallback control:%s | value: %s' % (args[0], args[1]))
        if radiocol == 'uiSetupNormalCol':
            self.uiValues.smoothNormal = args[1]
        elif radiocol == 'uiSetupFluxCol':
            self.uiValues.paintFlux = args[1]
        elif radiocol == 'uiSetupChkInputConn':
            # Maya callback sends a tuple back for checkbox but seems not a boolean and has to be processed???
            self.uiValues.preserveConn = getBoolFromMayaControl(args[1][0], self.mayaVersion)
        elif radiocol == 'uiSetupHierarchyActive':
            self.uiValues.hierarchy = getBoolFromMayaControl(args[1][0], self.mayaVersion)
        elif radiocol == 'uiSetupRealTimeRampFX':
            self.uiValues.realTimeRampFX = getBoolFromMayaControl(args[1][0], self.mayaVersion)
        elif radiocol == 'uiSetupHierarchySession':
            self.uiValues.group = 0.0
        elif radiocol == 'uiSetupHierarchyStroke':
            self.uiValues.group = 1.0
        elif radiocol == 'uiSetupHierarchySource':
            self.uiValues.group = 2.0
        elif radiocol == 'uiSetupContinuousTransform':
            self.uiValues.continuousTransform = getBoolFromMayaControl(args[1][0], self.mayaVersion)
        else:
            print(args)

        self.uiValues.commitVars()
        self.updateUIControls(self.uiValues)
        self.updateUISetupControls(self.uiValues)
        if sp3d_log:
            print("done updating SetupUI")


# -----------------------------------------------------------------------------------
#    UTILITIES
# -----------------------------------------------------------------------------------

def getBoolFromMayaControl(uicontrol, version):
    """
    return the bool state of the passed uicontrol, return false by default
    Maya returns control state as string pre-2011 and as bool 2011+
    """
    state = False
    if version - 2011 >= 0:
        # at least a maya 2011
        state = uicontrol
    else:
        # pre2011, UI controls were returning the state as string and not as a bool prior to 2011
        if uicontrol == 'true':
            state = True
    return state


def getMayaVersion():
    """
    attempt to detect the version of maya and return it as a numerical value.
    """
    version = cmds.about(v=True)
    supportedversion = False
    while not supportedversion:
        try:
            version = int(version[:4])
            supportedversion = True
        except ValueError:
            result = cmds.promptDialog(title='Enter Maya version',
                                       message='Couldn\'t determine the version of Maya\n, please enter the 4 digits of the maya version you are using (ie: 2011)',
                                       button=['OK', 'Cancel & Quit'], defaultButton='OK', cancelButton='Cancel & Quit',
                                       dismissString='Cancel & Quit')
            if result == 'OK':
                version = cmds.promptDialog(query=True, text=True)
            else:
                sys.exit()
    if version <= 2010:
        cmds.confirmDialog(title='Maya version alert',
                           message='This version of the script was updated for Maya 2011 and above.\nThere will be unexpected stuff happening with older versions, or not...')
    return version


def getDAGPath(node, depth=False):
    """
    Return the DAG path of the node argument (node must be a transform, if not, will attempt to locate its immediate parent and make sure it's a transform and will proceed from there)
    Return the extended DAG path to the node's shape when depth=True
    Return None if the node doesn't have any shape children, or more than one children shape.
    """
    dag = None
    nodetype = cmds.objectType(node)

    if nodetype != 'transform':
        # node is not a transform, will proceed upstream to its immediate parent and will verify if the parent is a transform
        tempdag = cmds.listRelatives(node, parent=True) or []
        if len(tempdag) == 1:  # node has a parent
            # node only has 1 parent, will proceed from there and see if it's a transform with a shape' child
            node = tempdag[0]
            nodetype = cmds.objectType(node)

    if nodetype == 'transform':
        # node is a transform, making sure it has only one children of shape type
        childlist = cmds.listRelatives(node, children=True, shapes=True) or []
        if len(childlist) == 1:
            # there's only 1 shape below the transform
            if depth:
                dag = cmds.listRelatives(node, fullPath=True, shapes=True)
            else:
                dag = cmds.listRelatives(node, path=True, shapes=True)

    if dag:
        return dag[0]
    else:
        return dag
