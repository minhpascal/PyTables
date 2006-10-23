"""
Test module for nested types under PyTables
===========================================

:Author:   Ivan Vilata
:Author:   Francesc Altet
:Contact:  ivilata@carabos.com
:Created:  2005-05-18
:License:  BSD
:Revision: $Id$
"""

import unittest

import numpy

import tables as t
import tables.tests.common as common
from tables.tests.common import verbose
from tables.IsDescription import Description
from tables.indexes import minRowIndex



# This is the structure of the table used for testing (DON'T PANIC!):
#
# +-+---------------------------------+-----+----------+-+-+
# |x|Info                             |color|info      |y|z|
# | +-----+--+----------------+----+--+     +----+-----+ | |
# | |value|y2|Info2           |name|z2|     |Name|Value| | |
# | |     |  +----+-----+--+--+    |  |     |    |     | | |
# | |     |  |name|value|y3|z3|    |  |     |    |     | | |
# +-+-----+--+----+-----+--+--+----+--+-----+----+-----+-+-+
#
# Please note that some fields are explicitly ordered while others are
# ordered alphabetically by name.

# The declaration of the nested table:
class Info(t.IsDescription):
    _v_pos = 3
    Name = t.StringCol(length=2)
    Value = t.Complex64Col()

class TestTDescr(t.IsDescription):

    """A description that has several nested columns."""

    x = t.Int32Col(0, shape=2, pos=0) #0
    y = t.Float64Col(1, shape=(2,2))
    z = t.UInt8Col(1)
    color = t.StringCol(2, " ", pos=2)
    info = Info()
    class Info(t.IsDescription): #1
        _v_pos = 1
        name = t.StringCol(length=2)
        value = t.Complex64Col(pos=0) #0
        y2 = t.Float64Col(1, pos=1) #1
        z2 = t.UInt8Col(1)
        class Info2(t.IsDescription):
            y3 = t.Time64Col(1, shape=2)
            z3 = t.EnumCol({'r':4, 'g':2, 'b':1}, 'r', shape=2)
            name = t.StringCol(length=2)
            value = t.Complex64Col(shape=2)

# The corresponding nested array description:
testADescr = [
    ('x', '(2,)Int32'),
    ('Info', [
        ('value', 'Complex64'),
        ('y2', 'Float64'),
        ('Info2', [
            ('name', 'a2'),
            ('value', '(2,)Complex64'),
            ('y3', '(2,)Float64'),
            ('z3', '(2,)UInt32')]),
        ('name', 'a2'),
        ('z2', 'UInt8')]),
    ('color', 'a2'),
    ('info', [
        ('Name', 'a2'),
        ('Value', 'Complex64')]),
    ('y', '(2,2)Float64'),
    ('z', 'UInt8')]

# The corresponding nested array description (brief version):
testADescr2 = [
    ('x', '(2,)i4'),
    ('Info', [
        ('value', '()c16'),
        ('y2', '()f8'),
        ('Info2', [
            ('name', '()S2'),
            ('value', '(2,)c16'),
            ('y3', '(2,)f8'),
            ('z3', '(2,)u4')]),
        ('name', '()S2'),
        ('z2', '()u1')]),
    ('color', '()S2'),
    ('info', [
        ('Name', '()S2'),
        ('Value', '()c16')]),
    ('y', '(2, 2)f8'),
    ('z', '()u1')]

# A nested array for testing:
testABuffer = [
    # x     Info                                                color info        y                  z
    #       value y2 Info2                            name z2         Name Value
    #                name   value    y3       z3
    ((3,2), (6j, 6., ('nn', (6j,4j), (6.,4.), (1,2)), 'NN', 8), 'cc', ('NN', 6j), ((6.,4.),(6.,4.)), 8),
    ((4,3), (7j, 7., ('oo', (7j,5j), (7.,5.), (2,1)), 'OO', 9), 'dd', ('OO', 7j), ((7.,5.),(7.,5.)), 9),
    ]
testAData = numpy.array(testABuffer, dtype=testADescr)
# The name of the column to be searched:
testCondCol = 'Info/z2'
# The name of a nested column (it can not be searched):
testNestedCol = 'Info'
# The condition to be applied on the column (all but the last row match it):
testCondition = '(2 < col) & (col < 9)'



def areDescriptionsEqual(desc1, desc2):
    """
    Are both `desc1` and `desc2` equivalent descriptions?

    The arguments may be description objects (``IsDescription``,
    ``Description``) or dictionaries.
    """

    if isinstance(desc1, t.Col):
        # This is a rough comparison but it suffices here.
        return (desc1.ptype == desc2.ptype
                and desc2.dtype == desc2.dtype
                and desc1._v_pos == desc2._v_pos
                and desc1.indexed == desc2.indexed
                #and desc1.dflt == desc2.dflt)
                and common.areArraysEqual(desc1.dflt, desc2.dflt))

    if hasattr(desc1, '_v_colObjects'):  # quacks like a Description
        cols1 = desc1._v_colObjects
    elif hasattr(desc1, 'columns'):  # quacks like an IsDescription
        cols1 = desc1.columns
    else:  # hope it quacks like a dictionary
        cols1 = desc1

    if hasattr(desc2, '_v_colObjects'):  # quacks like a Description
        cols2 = desc2._v_colObjects
    elif hasattr(desc2, 'columns'):  # quacks like an IsDescription
        cols2 = desc2.columns
    else:  # hope it quacks like a dictionary
        cols2 = desc2

    if len(cols1) != len(cols2):
        return False

    for (colName, colobj1) in cols1.iteritems():
        colobj2 = cols2[colName]
        if colName in ('_v_indexprops', '_v_pos'):
            # The comparison may not be quite exhaustive!
            return colobj1 == colobj2
        if not areDescriptionsEqual(colobj1, colobj2):
            return False

    return True



# Test creating nested column descriptions
class DescriptionTestCase(common.PyTablesTestCase):

    _TestTDescr = TestTDescr
    _testADescr = testADescr
    _testADescr2 = testADescr2
    _testAData = testAData

    def test00_instance(self):
        """Creating an instance of a nested description."""

        self._verboseHeader()
        self.assert_(
            areDescriptionsEqual(self._TestTDescr, self._TestTDescr()),
            "Table description does not match the given one.")

    def test01_instance(self):
        """Checking attrs of an instance of a nested description."""

        self._verboseHeader()
        descr = Description(self._TestTDescr().columns)
        if verbose:
            print "Generated description:", descr._v_nestedDescr
            print "Should look like:", self._testADescr2
        self.assert_(self._testADescr2 == descr._v_nestedDescr,
                     "Description._v_nestedDescr does not match.")



# Test creating a nested table and opening it
class CreateTestCase(common.TempFileMixin, common.PyTablesTestCase):

    _TestTDescr = TestTDescr
    _testABuffer = testABuffer
    _testAData = testAData


    def _checkColumns(self, cols, desc):
        """
        Check that `cols` has all the accessors for `self._TestTDescr`.
        """

        # ``_desc`` is a leaf column and ``cols`` a ``Column``.
        if isinstance(desc, t.Col):
            return isinstance(cols, t.Column)

        # ``_desc`` is a description object and ``cols`` a ``Cols``.
        descColumns = desc._v_colObjects
        for colName in descColumns:
            if colName not in cols._v_colnames:
                return False
            if not self._checkColumns(cols._f_col(colName),
                                      descColumns[colName]):
                return False

        return True


    def _checkDescription(self, table):
        """
        Check that description of `table` matches `self._TestTDescr`.
        """

        # Compare descriptions.
        self.assert_(
            areDescriptionsEqual(self._TestTDescr, table.description),
            "Table description does not match the given one.")
        # Check access to columns.
        self._checkColumns(table.cols, table.description)


    def _checkColinstances(self, table):
        """
        Check that ``colinstances`` and ``cols`` of `table` match.
        """
        for colpathname in table.description._v_pathnames:
            self.assert_( table.colinstances[colpathname]
                          is table.cols._f_col(colpathname) )


    def test00_create(self):
        """Creating a nested table."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        self._checkDescription(tbl)
        self._checkColinstances(tbl)


    def test01_open(self):
        """Opening a nested table."""

        self._verboseHeader()
        self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        self._reopen()
        tbl = self.h5file.root.test
        self._checkDescription(tbl)
        self._checkColinstances(tbl)


    def test02_NestedRecArrayCompat(self):
        """Creating a compatible ``NestedRecArray``."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        self.assert_(common.areArraysEqual(nrarr, self._testAData),
                     "Can not create a compatible record array.")


    def test03_NRA(self):
        """Creating a table from a NestedRecArray object."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._testAData, title=self._getMethodName())
        tbl.flush()
        readAData = tbl.read()
        if verbose:
            print "Read data:", readAData
            print "Should look like:", self._testAData
        self.assert_(common.areArraysEqual(self._testAData, readAData),
                     "Written and read values differ.")

    def test04_NRA2(self):
        """Creating a table from a generated NestedRecArray object."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        readAData = tbl.read()

        tbl2 = self.h5file.createTable(
            '/', 'test2', readAData, title=self._getMethodName())
        readAData2 = tbl2.read()

        self.assert_(common.areArraysEqual(self._testAData, readAData2),
                     "Written and read values differ.")


# Test writing data in a nested table
class WriteTestCase(common.TempFileMixin, common.PyTablesTestCase):

    _TestTDescr = TestTDescr
    _testAData = testAData
    _testCondition = testCondition
    _testCondCol = testCondCol
    _testNestedCol = testNestedCol

    def _testCondVars(self, table):
        """Get condition variables for the given `table`."""
        return {'col': table.cols._f_col(self._testCondCol)}


    def _testNestedCondVars(self, table):
        """Get condition variables for the given `table`."""
        return {'col': table.cols._f_col(self._testNestedCol)}


    def _appendRow(self, row, index):
        """
        Append the `index`-th row in `self._testAData` to `row`.

        Values are set field-by-field (be it nested or not).
        """

        record = self._testAData[index]
        for fieldName in self._testAData.dtype.names:
            row[fieldName] = record[fieldName]
        row.append()


    def test00_append(self):
        """Appending a set of rows."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        readAData = tbl.read()
        self.assert_(common.areArraysEqual(self._testAData, readAData),
                     "Written and read values differ.")


    def test01_row(self):
        """Appending individual rows."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        row = tbl.row
        # Add the first row
        self._appendRow(row, 0)
        # Add the rest of the rows field by field.
        for i in range(1, len(self._testAData)):
            self._appendRow(row, i)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        readAData = tbl.read()
        self.assert_(common.areArraysEqual(self._testAData, readAData),
                     "Written and read values differ.")


    def test02_where(self):
        """Searching nested data."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        searchedCoords = tbl.getWhereList(
            self._testCondition, self._testCondVars(tbl))

        # All but the last row match the condition.
        searchedCoords.sort()
        self.assertEqual(searchedCoords.tolist(),
                         range(len(self._testAData) - 1),
                         "Search returned incorrect results.")


    def test02b_whereAppend(self):
        """Searching nested data and appending it to another table."""

        self._verboseHeader()
        tbl1 = self.h5file.createTable(
            '/', 'test1', self._TestTDescr, title=self._getMethodName())
        tbl1.append(self._testAData)
        tbl1.flush()

        tbl2 = self.h5file.createTable(
            '/', 'test2', self._TestTDescr, title=self._getMethodName())
        tbl1.whereAppend(
            tbl2, self._testCondition, self._testCondVars(tbl1))

        if self.reopen:
            self._reopen()
            tbl1 = self.h5file.root.test1
            tbl2 = self.h5file.root.test2

        searchedCoords = tbl2.getWhereList(
            self._testCondition, self._testCondVars(tbl2))

        # All but the last row match the condition.
        searchedCoords.sort()
        self.assertEqual(searchedCoords.tolist(),
                         range(len(self._testAData) - 1),
                         "Search returned incorrect results.")


    def test03_colscond(self):
        """Searching on a column with nested columns."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        self.assertRaises(
            TypeError, tbl.getWhereList,
            self._testCondition, self._testNestedCondVars(tbl))


    def test04_modifyColumn(self):
        """Modifying one single nested column (modifyColumn)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        nColumn = self._testNestedCol
        # Get the nested column data and swap the first and last rows.
        raTable = self._testAData.copy()
        raColumn = raTable[nColumn]
        # The next will not work until NestedRecords supports copies
        (raColumn[0], raColumn[-1]) = (raColumn[-1], raColumn[0])

        # Write the resulting column and re-read the whole table.
        tbl.modifyColumn(colname=nColumn, column=raColumn)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        raReadTable = tbl.read()
        if verbose:
            print "Table read:", raReadTable
            print "Should look like:", raTable

        # Compare it to the written one.
        self.assert_(common.areArraysEqual(raTable, raReadTable),
                     "Written and read values differ.")

    def test05a_modifyColumns(self):
        """Modifying one nested column (modifyColumns)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        nColumn = self._testNestedCol
        # Get the nested column data and swap the first and last rows.
        raTable = self._testAData.copy()
        raColumn = raTable[nColumn]
        (raColumn[0], raColumn[-1]) = (raColumn[-1].copy(), raColumn[0].copy())
        newdtype = numpy.dtype([(nColumn, raTable.dtype.fields[nColumn][0])])

        # Write the resulting column and re-read the whole table.
        tbl.modifyColumns(names=[nColumn], columns=raColumn)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        raReadTable = tbl.read()
        if verbose:
            print "Table read:", raReadTable
            print "Should look like:", raTable

        # Compare it to the written one.
        self.assert_(common.areArraysEqual(raTable, raReadTable),
                     "Written and read values differ.")

    def test05b_modifyColumns(self):
        """Modifying two nested columns (modifyColumns)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        # Get the nested column data and swap the first and last rows.
        colnames = ['x', 'color']  # Get the first two columns
        raCols = numpy.rec.fromarrays([self._testAData['x'].copy(),
                                       self._testAData['color'].copy()],
                                      dtype=[('x','(2,)i4'),('color', '1a2')])
                               #descr=tbl.description._v_nestedDescr[0:2])
                               # or...
                               # names=tbl.description._v_nestedNames[0:2],
                               # formats=tbl.description._v_nestedFormats[0:2])
        (raCols[0], raCols[-1]) = (raCols[-1].copy(), raCols[0].copy())

        # Write the resulting columns
        tbl.modifyColumns(names=colnames, columns=raCols)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        # Re-read the appropriate columns
        raCols2 = numpy.rec.fromarrays([tbl.cols._f_col('x'),
                                        tbl.cols._f_col('color')],
                                       dtype=raCols.dtype)
        if verbose:
            print "Table read:", raCols2
            print "Should look like:", raCols

        # Compare it to the written one.
        self.assert_(common.areArraysEqual(raCols, raCols2),
                     "Written and read values differ.")

    def test06_modifyRows(self):
        "Checking modifying several rows at once (using nestedrecarray)"

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)
        tbl.flush()

        # Get the nested record and swap the first and last rows.
        raTable = self._testAData.copy()
        (raTable[0], raTable[-1]) = (raTable[-1].copy(), raTable[0].copy())

        # Write the resulting nested record and re-read the whole table.
        tbl.modifyRows(start=0, stop=2, rows=raTable)
        tbl.flush()

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        raReadTable = tbl.read()
        if verbose:
            print "Table read:", raReadTable
            print "Should look like:", raTable

        # Compare it to the written one.
        self.assert_(common.areArraysEqual(raTable, raReadTable),
                     "Written and read values differ.")

    def test07_index(self):
        """Checking indexes of nested columns"""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName(),
            expectedrows = minRowIndex*2)
        for i in range(minRowIndex):
            tbl.append(self._testAData)
        tbl.flush()
        coltoindex = tbl.cols._f_col(self._testCondCol)
        indexrows = coltoindex.createIndex(testmode=1)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test
            coltoindex = tbl.cols._f_col(self._testCondCol)

        if verbose:
            print "Number of written rows:", tbl.nrows
            print "Number of indexed rows:", coltoindex.index.nelements

        # Check indexing flags:
        self.assert_(tbl.indexed == True, "Table not indexed")
        self.assert_(coltoindex.index <> None, "Column not indexed")
        self.assert_(tbl.colindexed[self._testCondCol], "Column not indexed")
        # Do a look-up for values
        searchedCoords = tbl.getWhereList(
            self._testCondition, self._testCondVars(tbl))

        if verbose:
            print "Searched coords:", searchedCoords

        # All even rows match the condition.
        searchedCoords.sort()
        self.assertEqual(searchedCoords.tolist(), range(0, minRowIndex*2, 2),
                         "Search returned incorrect results.")


class WriteNoReopen(WriteTestCase):
    reopen = 0

class WriteReopen(WriteTestCase):
    reopen = 1


class ReadTestCase(common.TempFileMixin, common.PyTablesTestCase):

    _TestTDescr = TestTDescr
    _testABuffer = testABuffer
    _testAData = testAData
    _testNestedCol = testNestedCol


    def test00a_repr(self):
        """Checking representation of a nested Table"""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title="test00")
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        if verbose:
            print "str(tbl)-->", str(tbl)
            print "repr(tbl)-->", repr(tbl)

        self.assert_(str(tbl) == "/test (Table(2L,)) 'test00'")
        tblrepr = repr(tbl)
        # Remove the platform-dependent information (i.e. byteorder)
        tblrepr = "\n".join(tblrepr.split("\n")[:-2])+"\n"
        self.assert_(tblrepr == \
"""/test (Table(2L,)) 'test00'
  description := {
  "x": Int32Col(dflt=0, shape=(2,), pos=0, indexed=False),
  "Info": {
    "value": Complex64Col(dflt=0j, shape=(), pos=0),
    "y2": Float64Col(dflt=1.0, shape=(), pos=1, indexed=False),
    "Info2": {
      "name": StringCol(length=2, dflt='', shape=(), pos=0, indexed=False),
      "value": Complex64Col(dflt=0j, shape=(2,), pos=1),
      "y3": Time64Col(dflt=1.0, shape=(2,), pos=2, indexed=False),
      "z3": EnumCol(Enum({'r': 4, 'b': 1, 'g': 2}), 'r', dtype='UInt32', shape=(2,), pos=3, indexed=False)},
    "name": StringCol(length=2, dflt='', shape=(), pos=3, indexed=False),
    "z2": UInt8Col(dflt=1, shape=(), pos=4, indexed=False)},
  "color": StringCol(length=2, dflt=' ', shape=(), pos=2, indexed=False),
  "info": {
    "Name": StringCol(length=2, dflt='', shape=(), pos=0, indexed=False),
    "Value": Complex64Col(dflt=0j, shape=(), pos=1)},
  "y": Float64Col(dflt=1.0, shape=(2, 2), pos=4, indexed=False),
  "z": UInt8Col(dflt=1, shape=(), pos=5, indexed=False)}
""")


    def test00b_repr(self):
        """Checking representation of a root Column."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title="test00")
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        if verbose:
            print "str(tbl.cols.y)-->'%s'" % str(tbl.cols.y)
            print "repr(tbl.cols.y)-->'%s'" % repr(tbl.cols.y)

        self.assert_(str(tbl.cols.y) == \
                     "/test.cols.y (Column(2, 2), Float64, idx=None)")
        self.assert_(repr(tbl.cols.y) == \
                     "/test.cols.y (Column(2, 2), Float64, idx=None)")

    def test00c_repr(self):
        """Checking representation of a nested Column."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title="test00")
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        if verbose:
            print "str(tbl.cols.Info.z2)-->'%s'" % str(tbl.cols.Info.z2)
            print "repr(tbl.cols.Info.z2)-->'%s'" % repr(tbl.cols.Info.z2)

        self.assert_(str(tbl.cols.Info.z2) == \
                     "/test.cols.Info.z2 (Column(), UInt8, idx=None)")
        self.assert_(repr(tbl.cols.Info.z2) == \
                     "/test.cols.Info.z2 (Column(), UInt8, idx=None)")

    def test01_read(self):
        """Checking Table.read with subgroups with a range index with step."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.rec.array(testABuffer,
                                dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.read(start=0, step=2, field='Info')
        nrarrcols = nrarr['Info'][0::2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test02_read(self):
        """Checking Table.read with a nested Column."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        tblcols = tbl.read(start=0, step=2, field='Info/value')
        nrarr = numpy.rec.array(testABuffer,
                                dtype=tbl.description._v_nestedDescr)
        nrarrcols = nrarr['Info']['value'][0::2]
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

class ReadNoReopen(ReadTestCase):
    reopen = 0

class ReadReopen(ReadTestCase):
    reopen = 1


# Checking the Table.Cols accessor
class ColsTestCase(common.TempFileMixin, common.PyTablesTestCase):

    _TestTDescr = TestTDescr
    _testABuffer = testABuffer
    _testAData = testAData
    _testNestedCol = testNestedCol


    def test00a_repr(self):
        """Checking string representation of Cols."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title="test00")

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        if verbose:
            print "str(tbl.cols)-->", str(tbl.cols)
            print "repr(tbl.cols)-->", repr(tbl.cols)

        self.assert_(str(tbl.cols) == "/test.cols (Cols), 6 columns")
        self.assert_(repr(tbl.cols) == \
"""/test.cols (Cols), 6 columns
  x (Column(2,), ('int32',(2,)))
  Info (Cols(), Description)
  color (Column(), |S2)
  info (Cols(), Description)
  y (Column(2, 2), ('float64',(2, 2)))
  z (Column(), uint8)
""")

    def test00b_repr(self):
        """Checking string representation of nested Cols."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        if verbose:
            print "str(tbl.cols.Info)-->", str(tbl.cols.Info)
            print "repr(tbl.cols.Info)-->", repr(tbl.cols.Info)

        self.assert_(str(tbl.cols.Info) == "/test.cols.Info (Cols), 5 columns")
        self.assert_(repr(tbl.cols.Info) == \
"""/test.cols.Info (Cols), 5 columns
  value (Column(), complex128)
  y2 (Column(), float64)
  Info2 (Cols(), Description)
  name (Column(), |S2)
  z2 (Column(), uint8)
""")

    def test01a_f_col(self):
        """Checking cols._f_col() with a subgroup."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        tblcol = tbl.cols._f_col(self._testNestedCol)
        if verbose:
            print "Column group name:", tblcol._v_desc._v_pathname
        self.assert_(tblcol._v_desc._v_pathname == self._testNestedCol,
                     "Column group name doesn't match.")

    def test01b_f_col(self):
        """Checking cols._f_col() with a column."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        tblcol = tbl.cols._f_col(self._testNestedCol+"/name")
        if verbose:
            print "Column name:", tblcol.name
        self.assert_(tblcol.name == "name",
                     "Column name doesn't match.")

    def test01c_f_col(self):
        """Checking cols._f_col() with a nested subgroup."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        tblcol = tbl.cols._f_col(self._testNestedCol+"/Info2")
        if verbose:
            print "Column group name:", tblcol._v_desc._v_pathname
        self.assert_(tblcol._v_desc._v_pathname == self._testNestedCol+"/Info2",
                     "Column group name doesn't match.")

    def test02a__len__(self):
        """Checking cols.__len__() in root level."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        length = len(tbl.cols)
        if verbose:
            print "Column group length:", length
        self.assert_(length == 6,
                     "Column group length doesn't match.")

    def test02b__len__(self):
        """Checking cols.__len__() in subgroup level."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        length = len(tbl.cols.Info)
        if verbose:
            print "Column group length:", length
        self.assert_(length == 5,
                     "Column group length doesn't match.")

    def test03a__getitem__(self):
        """Checking cols.__getitem__() with a single index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols[1]
        nrarrcols = nrarr[1]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test03b__getitem__(self):
        """Checking cols.__getitem__() with a range index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols[0:2]
        nrarrcols = nrarr[0:2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test03c__getitem__(self):
        """Checking cols.__getitem__() with a range index with step."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols[0::2]
        nrarrcols = nrarr[0::2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")


    def test04a__getitem__(self):
        """Checking cols.__getitem__() with subgroups with a single index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info')[1]
        nrarrcols = nrarr['Info'][1]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test04b__getitem__(self):
        """Checking cols.__getitem__() with subgroups with a range index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info')[0:2]
        nrarrcols = nrarr['Info'][0:2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test04c__getitem__(self):
        """Checking cols.__getitem__() with subgroups with a range index with step."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info')[0::2]
        nrarrcols = nrarr['Info'][0::2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test05a__getitem__(self):
        """Checking cols.__getitem__() with a column with a single index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info/value')[1]
        nrarrcols = nrarr['Info']['value'][1]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(nrarrcols == tblcols,
                     "Original array are retrieved doesn't match.")

    def test05b__getitem__(self):
        """Checking cols.__getitem__() with a column with a range index."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info/value')[0:2]
        nrarrcols = nrarr['Info']['value'][0:2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")

    def test05c__getitem__(self):
        """Checking cols.__getitem__() with a column with a range index with step."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', self._TestTDescr, title=self._getMethodName())
        tbl.append(self._testAData)

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        nrarr = numpy.array(testABuffer, dtype=tbl.description._v_nestedDescr)
        tblcols = tbl.cols._f_col('Info/value')[0::2]
        nrarrcols = nrarr['Info']['value'][0::2]
        if verbose:
            print "Read cols:", tblcols
            print "Should look like:", nrarrcols
        self.assert_(common.areArraysEqual(nrarrcols, tblcols),
                     "Original array are retrieved doesn't match.")


class ColsNoReopen(ColsTestCase):
    reopen = 0

class ColsReopen(ColsTestCase):
    reopen = 1


class Nested(t.IsDescription):
    uid = t.IntCol(pos=1)
    value = t.FloatCol(pos=2)

class A_Candidate(t.IsDescription):
    nested1 = Nested()
    nested2 = Nested()

class B_Candidate(t.IsDescription):
    nested1 = Nested
    nested2 = Nested

class C_Candidate(t.IsDescription):
    nested1 = Nested()
    nested2 = Nested

Dnested = {'uid': t.IntCol(pos=1),
           'value': t.FloatCol(pos=2),
           }

D_Candidate = {"nested1": Dnested,
               "nested2": Dnested,
               }

E_Candidate = {"nested1": Nested,
               "nested2": Dnested,
               }

F_Candidate = {"nested1": Nested(),
               "nested2": Dnested,
               }

# Checking several nested columns declared in the same way
class SameNestedTestCase(common.TempFileMixin, common.PyTablesTestCase):

    correct_names = ['',  # The root of columns
                     'nested1', 'nested1/uid', 'nested1/value',
                     'nested2', 'nested2/uid', 'nested2/value']

    def test01a(self):
        """Checking same nested columns (instance flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', A_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")

    def test01b(self):
        """Checking same nested columns (class flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', B_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")

    def test01c(self):
        """Checking same nested columns (mixed instance/class flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', C_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")

    def test01d(self):
        """Checking same nested columns (dictionary flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', D_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")

    def test01e(self):
        """Checking same nested columns (mixed dictionary/class flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', E_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")

    def test01f(self):
        """Checking same nested columns (mixed dictionary/instance flavor)."""

        self._verboseHeader()
        tbl = self.h5file.createTable(
            '/', 'test', F_Candidate, title=self._getMethodName())

        if self.reopen:
            self._reopen()
            tbl = self.h5file.root.test

        names = [col._v_pathname for col in tbl.description._f_walk(type="All")]
        if verbose:
            print "Pathnames of columns:", names
            print "Should look like:", self.correct_names
        self.assert_(names == self.correct_names,
                     "Column nested names doesn't match.")


class SameNestedNoReopen(SameNestedTestCase):
    reopen = 0

class SameNestedReopen(SameNestedTestCase):
    reopen = 1



#----------------------------------------------------------------------

def suite():
    """Return a test suite consisting of all the test cases in the module."""

    theSuite = unittest.TestSuite()
    niter = 1
    #heavy = 1  # uncomment this only for testing purposes

    #theSuite.addTest(unittest.makeSuite(DescriptionTestCase))
    #theSuite.addTest(unittest.makeSuite(WriteReopen))
    for i in range(niter):
        theSuite.addTest(unittest.makeSuite(DescriptionTestCase))
        theSuite.addTest(unittest.makeSuite(CreateTestCase))
        theSuite.addTest(unittest.makeSuite(WriteNoReopen))
        theSuite.addTest(unittest.makeSuite(WriteReopen))
        theSuite.addTest(unittest.makeSuite(ColsNoReopen))
        theSuite.addTest(unittest.makeSuite(ColsReopen))
        theSuite.addTest(unittest.makeSuite(ReadNoReopen))
        theSuite.addTest(unittest.makeSuite(ReadReopen))
        theSuite.addTest(unittest.makeSuite(SameNestedNoReopen))
        theSuite.addTest(unittest.makeSuite(SameNestedReopen))

    return theSuite


if __name__ == '__main__':
    unittest.main( defaultTest='suite' )



## Local Variables:
## mode: python
## py-indent-offset: 4
## tab-width: 4
## fill-column: 72
## End:
