import rhinoscriptsyntax as rs

import rhinoscriptsyntax as rs

class DeleteDocumentData:
    def __init__(self):
        result = rs.MessageBox("Really delete document data?", 1)
        if result: 
            print "deleting all document data"
            rs.DeleteDocumentData()

if __name__ == '__main__':
    DeleteDocumentData()
