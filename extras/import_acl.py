import sqlite3 as lite
from tldextract import extract as e
 
con = lite.connect('/home/jaime/.eilat/eilat.db')
print(con)
cur = con.cursor()
print(cur)

with open("acl/new.acl", "r") as acl_file:
    for line in acl_file.readlines():
        r = e(line.lstrip('.').rstrip())
        query = "insert or ignore into blacklist values('%s', '%s', '%s')" % (r.subdomain, r.domain, r.suffix)
        print(query)
        try:
            cur.execute(query)
        except lite.IntegrityError as exc:
            print(exc)

cur.execute("update blacklist set subdomain = NULL where subdomain = ''")
con.commit()
