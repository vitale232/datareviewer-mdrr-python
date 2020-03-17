# Copyright 2017-2018 by Esri

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class ToolValidator:
    """Class for validating a tool's parameter values and controlling
    the behavior of the tool's dialog."""

    def __init__(self):
        """Setup arcpy and the list of tool parameters."""
        import arcpy
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        """Refine the properties of a tool's parameters.    This method is
        called when the tool is opened."""
        self.params[1].parameterDependencies = [0]
        self.params[2].parameterDependencies = [0]
        self.params[3].parameterDependencies = [2]
        self.params[5].parameterDependencies = [4]

        return

    def table_path_from_wildcard(self, wildcard):
        """Take a wildcard expression and try to find a single table that matches.
        If a single match IS found, the matching table is joined to the arcpy workspace

        This method expects the `arcpy.env.workspace` has been set to the reviewer GDB.

        If a single match IS NOT found, this method returns an empty string.
        When an empty string is passed to `arcpy.Exists`, it returns `False`."""
        import os

        tables = arcpy.ListTables(wildcard)

        if len(tables) == 1:
            return os.path.join(arcpy.env.workspace, tables[0])
        else:
            return ''

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed.    This method is called whenever a parmater
        has been changed."""
        RevDB = self.params[0].value
        original_ws = arcpy.env.workspace

        if RevDB:
            arcpy.env.workspace = RevDB
            SessionsTable = self.table_path_from_wildcard('*GDB_REVSESSIONTABLE')
            if not arcpy.Exists(SessionsTable):
                SessionsTable = self.table_path_from_wildcard('*REVSESSIONTABLE')
                # `arcpy.ListTables` does not recognize the GDB_REVSESSIONTABLE for in a file
                # geodatabase for some reason. If the table still doesn't exist, assume
                # its a fgdb and try to build the path manually as a workaround
                if not arcpy.Exists(SessionsTable):
                    import os
                    SessionsTable = os.path.join(arcpy.env.workspace, 'GDB_REVSESSIONTABLE')
                    if not arcpy.Exists(SessionsTable):
                        SessionsTable = os.path.join(arcpy.env.workspace, 'REVSESSIONTABLE')

            MainTable = self.table_path_from_wildcard('*REVTABLEMAIN')

            if arcpy.Exists(SessionsTable) and arcpy.Exists(MainTable):

                children = []

                with arcpy.da.SearchCursor(SessionsTable, ("SESSIONNAME")) as rows:
                    for row in rows:
                        children.append(row[0])

                self.params[1].filter.list    = children

                self.params[2].value = MainTable
                self.params[2].enabled = False

                if not self.params[4].value:
                    # Out reviewer workspace not currently set, default to input workspace
                    self.params[4].value = str(RevDB)

        OutRevDB = self.params[4].value

        if OutRevDB:
            arcpy.env.workspace = OutRevDB

            SessionsTable = self.table_path_from_wildcard("*GDB_REVSESSIONTABLE")
            if not arcpy.Exists(SessionsTable):
                SessionsTable = self.table_path_from_wildcard("*REVSESSIONTABLE")
                # `arcpy.ListTables` does not recognize the GDB_REVSESSIONTABLE for in a file
                # geodatabase for some reason. If the table still doesn't exist, assume
                # its a fgdb and try to build the path manually as a workaround
                if not arcpy.Exists(SessionsTable):
                    import os
                    SessionsTable = os.path.join(arcpy.env.workspace, 'GDB_REVSESSIONTABLE')
                    if not arcpy.Exists(SessionsTable):
                        SessionsTable = os.path.join(arcpy.env.workspace, 'REVSESSIONTABLE')
            if arcpy.Exists(SessionsTable):
                children = []

                with arcpy.da.SearchCursor(SessionsTable, ("SESSIONNAME")) as rows:
                    for row in rows:
                        children.append(row[0])

                self.params[5].filter.list = children

        arcpy.env.workspace = original_ws
        return

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.    This method is called after internal validation."""
        #Check if input and output databases are Reviewer Databases
        RevDB = self.params[0].value
        OutRevDB = self.params[4].value

        original_ws = arcpy.env.workspace
        arcpy.env.workspace = RevDB

        if RevDB:
            MainTable = self.table_path_from_wildcard("*REVTABLEMAIN")
            if arcpy.Exists(MainTable):
                fields =[x.name.upper() for x in arcpy.ListFields(MainTable)]
                if "LIFECYCLEPHASE" not in fields:
                    self.params[0].setIDMessage("Error", "090034")
                elif self.params[1].filter.list is None or len(self.params[1].filter.list) < 1:
                    self.params[0].setErrorMessage("Input Reviewer Workspace does not contain any sessions.")
            else:
                self.params[0].setErrorMessage("Selected database is not a Reviewer-enabled workspace.")
        if OutRevDB:
            OutMainTable = self.table_path_from_wildcard("*REVTABLEMAIN")
            if arcpy.Exists(OutMainTable):
                fields = [x.name.upper() for x in arcpy.ListFields(OutMainTable)]
                if "LIFECYCLEPHASE" not in fields:
                    self.params[4].setIDMessage("Error", "090034")
                elif self.params[5].filter.list is None or len(self.params[5].filter.list) < 1:
                    self.params[4].setErrorMessage("Output Reviewer Workspace does not contain any sessions.")
            else:
                self.params[4].setErrorMessage("Selected database is not a Reviewer-enabled workspace.")
        if RevDB and OutRevDB:
            if str(RevDB) == str(OutRevDB):
                if self.params[6].value == False:
                    self.params[6].setWarningMessage("Copying records between sessions but not deleting will cause duplicate records in the Reviewer Workspace.")

        arcpy.env.workspace = original_ws
        return
