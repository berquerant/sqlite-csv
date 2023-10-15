from contextlib import contextmanager
from tempfile import TemporaryDirectory
from dataclasses import dataclass
import os
import subprocess
import unittest


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

    @contextmanager
    def prepare_data(self):
        tables = [self.account, self.address]
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
                    name="join accounst and addresses",
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
