import rhinoscriptsyntax as rs

class EditDocumentData:
    def __init__(self):
        rows = []
        count = 0
        sections = []
        keys = []
        for section in rs.GetDocumentData(section=None, entry=None):
            for entry in rs.GetDocumentData(section=section):
                str = "[%s] %s = %s" % (section, 
                                        entry,
                                        rs.GetDocumentData(section=section, entry=entry))
                rows.append(str)
                sections.append(section)
                keys.append(entry)

        choice = rs.ListBox(rows, "select")

        if not choice:
            print "no choice selected"
        else:
            count = 0
            for row in rows:
                if choice == rows[count]:
                    break
                count += 1

            text = rs.EditBox(message="Edit %s" % rows[count])
            if text: 
                print "updating %s :: %s" % (sections[count], keys[count])
                rs.SetDocumentData(sections[count], keys[count], text)

if __name__ == '__main__':
    EditDocumentData()
