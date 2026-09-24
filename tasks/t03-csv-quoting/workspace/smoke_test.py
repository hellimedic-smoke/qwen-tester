from csvparse import parse_csv

rows = parse_csv('name,note\n"Smith, John",hello\n')
assert rows == [["name", "note"], ["Smith, John", "hello"]], rows
print("smoke tests passed")
