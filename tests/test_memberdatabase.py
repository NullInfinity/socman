"""
test_memberdatabase.py contains the automated tests for socman.MemberDatabase.

Tests on socman should be run with `python -m pytest`. To run just these tests,
run `pytest tests/test_MemberDatabase.py`.


The MIT License (MIT)

Copyright (c) 2016 Alexander Thorne

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import collections
import datetime
import unittest
import unittest.mock
import pytest

import socman


@pytest.fixture
def mocks():
    """Fixture for mocked sqlite3.connect and datetime functions."""
    sql_connect_patcher = unittest.mock.patch('socman.sqlite3.connect')

    date_patcher = unittest.mock.patch('socman.date')
    date_mock = date_patcher.start()
    date_mock.today.return_value = datetime.date.min

    datetime_patcher = unittest.mock.patch('socman.datetime')
    datetime_mock = datetime_patcher.start()
    datetime_mock.utcnow.return_value = datetime.datetime.min

    # note that date and datetime mocks are never used
    # they are simply created so the values of date.min and datetime.utcnow
    # can be controlled
    yield collections.namedtuple('mock_type', 'sql_connect date datetime')(
            sql_connect_patcher.start(), date_mock, datetime_mock)

    sql_connect_patcher.stop()
    datetime_patcher.stop()
    date_patcher.stop()


@pytest.fixture
def mdb(mocks):
    mdb_fixture = socman.MemberDatabase('test.db', safe=True)
    mdb_fixture._mocksql_connect = mocks.sql_connect
    yield mdb_fixture


def test_db_connect(mdb):
    """Test MemberDatabase.__init__ calls sqlite3.connect."""
    mdb._mocksql_connect.assert_called_with('test.db')


def test_optional_commit_on(mocks):
    """Test MemberDatabase.optional_commit commits to DB when safe=True."""
    mdb = socman.MemberDatabase('test.db', safe=True)
    mdb.optional_commit()
    assert mocks.sql_connect().commit.called


def test_optional_commit_off(mocks):
    """Test MemberDatabase.optional_commit does not commit to DB when safe=False."""
    mdb = socman.MemberDatabase('test.db', safe=False)
    mdb.optional_commit()
    assert not mocks.sql_connect().commit.called


# exception=None means member is present and will be found
# suffix on each comment description will contain either AF, TS, both or none
#   AF = autofix enabled
#   TS = update_timestamp enabled
@pytest.mark.parametrize("args,mock_returns,expected_return,exception,calls", [
    (   # member with no name or barcode (so not present!)
        {
            'member': socman.Member(None, None),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [],
            [],
            ],
        None,
        socman.BadMemberError,
        {
            'values': [],
            'count': {
                'execute': 0,
                'fetchall': 0,
                'commit': 0
                },
            }
        ),

    (   # member with no name or barcode (so not present!) AF
        {
            'member': socman.Member(None, None),
            'autofix': True,
            'update_timestamp': False,
            },
        [
            [],
            [],
            ],
        None,
        socman.BadMemberError,
        {
            'values': [],
            'count': {
                'execute': 0,
                'fetchall': 0,
                'commit': 0
                },
            }
        ),

    (   # member with no name or barcode (so not present!) TS
        {
            'member': socman.Member(None, None),
            'autofix': False,
            'update_timestamp': True,
            },
        [
            [],
            [],
            ],
        None,
        socman.BadMemberError,
        {
            'values': [],
            'count': {
                'execute': 0,
                'fetchall': 0,
                'commit': 0
                },
            }
        ),

    (   # member with no name or barcode (so not present!) AFTS
        {
            'member': socman.Member(None, None),
            'autofix': True,
            'update_timestamp': True,
            },
        [
            [],
            [],
            ],
        None,
        socman.BadMemberError,
        {
            'values': [],
            'count': {
                'execute': 0,
                'fetchall': 0,
                'commit': 0
                },
            }
        ),

    (   # member not present in DB under barcode or name
        {
            'member': socman.Member('00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [],
            [],
            ],
        None,
        socman.MemberNotFoundError,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 2,
                'commit': 0
                },
            }
        ),

     (   # member not present in DB under barcode
        {
            'member': socman.Member('00000000',
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [],
            [],
            ],
        None,
        socman.MemberNotFoundError,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 0
                },
            }
        ),

    (   # member not present in DB under name
        {
            'member': socman.Member(barcode=None,
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [],
            [],
            ],
        None,
        socman.MemberNotFoundError,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 0
                },
            }
        ),

    (   # member with barcode only
        # present (and unique) in DB under barcode
        {
            'member': socman.Member(barcode='00000000',
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with barcode only
        # present (and unique) in DB under barcode [TS]
        {
            'member': socman.Member(barcode='00000000',
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE barcode=?""",
                    (datetime.date.min, '00000000')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with barcode only
        # present (and unique) in DB under barcode [AF]
        {
            'member': socman.Member(barcode='00000000',
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with barcode only
        # present (and unique) in DB under barcode [TSAF]
        {
            'member': socman.Member(barcode='00000000',
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE barcode=?""",
                    (datetime.date.min, '00000000')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under barcode
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under barcode [TS]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE barcode=?""",
                    (datetime.date.min, '00000000')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under barcode [AF]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """UPDATE users SET firstName=?,lastName=? """
                    """WHERE barcode=?""",
                    ('Ted', 'Bobson', '00000000')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under barcode [TSAF]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000',)
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE barcode=?""",
                    (datetime.date.min, '00000000')
                    ),
                unittest.mock.call(
                    """UPDATE users SET firstName=?,lastName=? """
                    """WHERE barcode=?""",
                    ('Ted', 'Bobson', '00000000')
                    ),
                ],
            'count': {
                'execute': 3,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name only
        # present (and unique) in DB under name
        {
            'member': socman.Member(barcode=None,
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name only
        # present (and unique) in DB under name [AF]
        {
            'member': socman.Member(barcode=None,
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': False,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 1,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name only
        # present (and unique) in DB under name [TS]
        {
            'member': socman.Member(barcode=None,
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE firstName=? AND lastName=?""",
                    (datetime.date.min, 'Ted', 'Bobson'),
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name only
        # present (and unique) in DB under name [TSAF]
        {
            'member': socman.Member(barcode=None,
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': True,
            },
        [
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE firstName=? AND lastName=?""",
                    (datetime.date.min, 'Ted', 'Bobson'),
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 1,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under *name*
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': False,
            },
        [
            [],
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000', )
                    ),
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 2,
                'fetchall': 2,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under *name* [TS]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': False,
            'update_timestamp': True,
            },
        [
            [],
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000', )
                    ),
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE firstName=? AND lastName=?""",
                    (datetime.date.min, 'Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 3,
                'fetchall': 2,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under *name* [AF]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': False,
            },
        [
            [],
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000', )
                    ),
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET barcode=? """
                    """WHERE firstName=? AND lastName=?""",
                    ('00000000', 'Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 3,
                'fetchall': 2,
                'commit': 1
                },
            }
        ),

    (   # member with name and barcode
        # present (and unique) in DB under *name* [TSAF]
        {
            'member': socman.Member(barcode='00000000',
                                    name=socman.Name('Ted', 'Bobson'),
                                    college='Wolfson'),
            'autofix': True,
            'update_timestamp': True,
            },
        [
            [],
            [('Ted', 'Bobson')],
            ],
        ('Ted', 'Bobson'),
        None,
        {
            'values': [
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE barcode=?""",
                    ('00000000', )
                    ),
                unittest.mock.call(
                    """SELECT firstName,lastName FROM users """
                    """WHERE firstName=? AND lastName=?""",
                    ('Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET last_attended=? """
                    """WHERE firstName=? AND lastName=?""",
                    (datetime.date.min, 'Ted', 'Bobson')
                    ),
                unittest.mock.call(
                    """UPDATE users SET barcode=? """
                    """WHERE firstName=? AND lastName=?""",
                    ('00000000', 'Ted', 'Bobson')
                    ),
                ],
            'count': {
                'execute': 4,
                'fetchall': 2,
                'commit': 1
                },
            }
        ),
     ])
def test_get_member(mdb, args, mock_returns, expected_return, exception, calls):
    mdb._mocksql_connect().cursor().fetchall.side_effect = mock_returns

    if not exception:
        assert expected_return == mdb.get_member(**args)
    else:
        with pytest.raises(exception):
            mdb.get_member(**args)
    mdb._mocksql_connect().cursor().execute.assert_has_calls(calls['values'])
    assert calls['count']['execute'] == mdb._mocksql_connect().cursor().execute.call_count
    assert calls['count']['fetchall'] == mdb._mocksql_connect().cursor().fetchall.call_count
    assert calls['count']['commit'] == mdb._mocksql_connect().commit.call_count


class MemberDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.first_name = 'Ted'
        self.last_name = 'Bobson'
        self.barcode = '00000000'
        self.college = 'Wolfson'
        self.member = socman.Member(self.barcode, socman.Name(self.first_name, self.last_name), college = self.college)
        self.member_nobarcode = socman.Member(None, socman.Name(self.first_name, self.last_name), college = self.college)

        self.mocksql_connect_patcher = unittest.mock.patch('socman.sqlite3.connect')
        self.mocksql_connect = self.mocksql_connect_patcher.start()
        self.addCleanup(self.mocksql_connect_patcher.stop)

        self.mdb = socman.MemberDatabase('test.db', safe=True)


    def test_add_member_none(self):
        with self.assertRaises(socman.BadMemberError):
            self.mdb.add_member(member=socman.Member(None))

    def test_add_member_present(self):
        self.mocksql_connect().cursor().fetchall.return_value = [(self.first_name, self.last_name)]
        self.mdb.add_member(self.member)
        self.assertEqual(3, self.mocksql_connect().cursor().execute.call_count)

    def test_add_member_present_by_name(self):
        self.mocksql_connect().cursor().fetchall.side_effect = [[], (self.first_name, self.last_name)]
        self.mdb.add_member(self.member)
        self.assertEqual(4, self.mocksql_connect().cursor().execute.call_count)

    @unittest.mock.patch('socman.datetime')
    @unittest.mock.patch('socman.date')
    def test_add_member_new(self, mock_date, mock_datetime):
        self.mocksql_connect().cursor().fetchall.side_effect = [[], [], [(self.first_name, self.last_name)]]
        mock_date.today.return_value = datetime.date.min
        mock_datetime.utcnow.return_value = datetime.datetime.min

        self.mdb.add_member(self.member)
        self.mocksql_connect().cursor().execute.assert_called_with('INSERT INTO users (barcode, firstName, lastName, college, datejoined, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (self.barcode, self.first_name, self.last_name, self.college, datetime.date.min, datetime.datetime.min, datetime.datetime.min))
        self.assertEqual(3, self.mocksql_connect().cursor().execute.call_count)

if __name__ == '__main__':
    unittest.main()
