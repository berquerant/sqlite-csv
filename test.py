import os
import subprocess
import unittest
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import TemporaryDirectory


class TableData:
    tablename: str
    data: str  # csv
    filename: str | None = None

    def __init__(self, tablename: str, data: str):
        self.tablename = tablename
        self.data = data

    def write_into(self, dirname: str):
        self.filename = f"{dirname}/{self.tablename}.csv"
        with open(self.filename, "w") as f:
            f.write(self.data)


@dataclass
class Command:
    """sqlite-csv.sh executor."""

    cmd: str

    @staticmethod
    def default() -> "Command":
        d = os.path.dirname(__file__)
        return Command(cmd=f"{d}/sqlite-csv.sh")

    def run(self, input: str | None, args: list[str]) -> str:
        return subprocess.run(
            [self.cmd, *args],
            input=input,
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout


#
# tables
#

accounts = """id,name,address_id
1,Alice,10
2,Bob,11
3,Charlie,10
"""

addresses = """id,name
10,America
11,Brazil
12,Canada
"""


class Data:
    def __init__(self):
        self.account = TableData(tablename="accounts", data=accounts)
        self.address = TableData(tablename="addresses", data=addresses)
        self.extensions = TableData(tablename="ext.json", data=accounts)
        self.numeric = TableData(tablename="20231212", data=addresses)

    @contextmanager
    def prepare_data(self):
        tables = [self.account, self.address, self.extensions, self.numeric]
        with TemporaryDirectory() as tmpdir:
            for t in tables:
                t.write_into(tmpdir)
            yield tmpdir


@dataclass
class Case:
    name: str
    args: list[str]
    want: str
    input: str | None = None


class SQLiteCSVTest(unittest.TestCase):
    def test_sqlite_csv(self):
        cmd = Command.default()
        data = Data()

        def test(c: Case):
            got = cmd.run(input=c.input, args=c.args)
            self.assertEqual(got.rstrip(), c.want.rstrip())

        with data.prepare_data():
            cases = [
                Case(
                    name="join extensions and numeric index",
                    args=[
                        "--index-headers",
                        "select `ext.json`.`0`, `ext.json`.`2`, `20231212`.`1` "
                        "from `ext.json` inner join `20231212` on `20231212`.`0` = `ext.json`.`2`",
                        data.extensions.filename,
                        data.numeric.filename,
                    ],
                    want="\n".join(
                        [
                            "0,2,1",
                            "1,10,America",
                            "2,11,Brazil",
                            "3,10,America",
                        ]
                    ),
                ),
                Case(
                    name="join extensions and numeric",
                    args=[
                        "select `ext.json`.`id`, `ext.json`.`address_id`, `20231212`.`name` "
                        "from `ext.json` inner join `20231212` on `20231212`.`id` = `ext.json`.`address_id`",
                        data.extensions.filename,
                        data.numeric.filename,
                    ],
                    want="\n".join(
                        [
                            "id,address_id,name",
                            "1,10,America",
                            "2,11,Brazil",
                            "3,10,America",
                        ]
                    ),
                ),
                Case(
                    name="select numeric all",
                    args=[
                        "select * from `20231212`",
                        data.numeric.filename,
                    ],
                    want=data.numeric.data,
                ),
                Case(
                    name="select extensions all",
                    args=[
                        "select * from `ext.json`",
                        data.extensions.filename,
                    ],
                    want=data.extensions.data,
                ),
                Case(
                    name="select accounts without header",
                    args=[
                        "--index-headers",
                        "select `1` from accounts",
                        data.account.filename,
                    ],
                    want="\n".join(
                        [
                            "1",
                            "Alice",
                            "Bob",
                            "Charlie",
                        ]
                    ),
                ),
                Case(
                    name="select accounts all without header",
                    args=[
                        "--index-headers",
                        "select * from accounts",
                        data.account.filename,
                    ],
                    want=data.account.data.replace("id,name,address_id", "0,1,2"),
                ),
                Case(
                    name="select accounts all",
                    args=["select * from accounts", data.account.filename],
                    want=data.account.data,
                ),
                Case(
                    name="select accounts Bob",
                    args=["select * from accounts where id = 2", data.account.filename],
                    want="\n".join(
                        [
                            "id,name,address_id",
                            "2,Bob,11",
                        ]
                    ),
                ),
                Case(
                    name="select accounts all from stdin",
                    args=["select * from stdin", "-"],
                    input=data.account.data,
                    want=data.account.data,
                ),
                Case(
                    name="join accounts and addresses",
                    args=[
                        "select * from accounts inner join addresses on accounts.address_id = addresses.id",
                        data.account.filename,
                        data.address.filename,
                    ],
                    want="\n".join(
                        [
                            "id,name,address_id,id,name",
                            "1,Alice,10,10,America",
                            "2,Bob,11,11,Brazil",
                            "3,Charlie,10,10,America",
                        ],
                    ),
                ),
                Case(
                    name="join accounts and addresses from stdin",
                    args=[
                        "select * from accounts inner join stdin on accounts.address_id = stdin.id",
                        data.account.filename,
                        "-",
                    ],
                    input=data.address.data,
                    want="\n".join(
                        [
                            "id,name,address_id,id,name",
                            "1,Alice,10,10,America",
                            "2,Bob,11,11,Brazil",
                            "3,Charlie,10,10,America",
                        ],
                    ),
                ),
            ]
            for c in cases:
                with self.subTest(msg=c.name):
                    test(c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
