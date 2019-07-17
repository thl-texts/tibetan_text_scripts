Attribute VB_Name = "NewMacros"
Sub GotoPage()
Attribute GotoPage.VB_ProcData.VB_Invoke_Func = "Normal.NewMacros.GotoPage"
'
' GotoPage Macro
'
'
    Selection.GoTo What:=wdGoToPage, Which:=wdGoToFirst, Count:=2, Name:=""
    Selection.Find.ClearFormatting
    With Selection.Find
        .Text = ""
        .Replacement.Text = ""
        .Forward = True
        .Wrap = wdFindContinue
        .Format = False
        .MatchCase = False
        .MatchWholeWord = False
        .MatchWildcards = False
        .MatchSoundsLike = False
        .MatchAllWordForms = False
    End With
    Selection.MoveLeft Unit:=wdCharacter, Count:=1
    Selection.Font.Name = "Times New Roman"
    Selection.Font.Size = 24
    Selection.Font.Name = "Times New Roman"
    Selection.Font.Size = 24
    Selection.TypeText Text:="[page 2]"
End Sub

Sub InsertPageMarkers()
'
' Insert XML like page markers
'
'
    For pn = ActiveDocument.Range.Information(wdNumberOfPagesInDocument) To 1 Step -1
        Selection.GoTo What:=wdGoToPage, Which:=wdGoToFirst, Count:=pn, Name:=""
        Selection.Font.Name = "Times New Roman"
        Selection.Font.Size = 24
        Selection.TypeText Text:="[page " & pn & "]"
    Next pn

End Sub

Sub DoDocsInInFolder()
    Dim vDirectory, nmlst As String
    Dim oDoc As Document
    
    vDirectory = InputBox("Enter Full Directory Path to the folder with documents to convert", "In Folder Location")
    outDir = InputBox("Enter Full Directory Path to the out folder to put documents in", "Out Folder Location")
    vFile = Dir(vDirectory & "\*.doc")
    nmlst = ""
    Do While vFile <> ""
        Set oDoc = Documents.Open(vDirectory & "\" & vFile)
        oDoc.Activate
        For pn = oDoc.Range.Information(wdNumberOfPagesInDocument) To 1 Step -1
            Selection.GoTo What:=wdGoToPage, Which:=wdGoToFirst, Count:=pn, Name:=""
            Selection.Font.Name = "Times New Roman"
            Selection.Font.Size = 24
            Selection.TypeText Text:="[page " & pn & "]"
        Next pn
        oDoc.SaveAs2 FileName:=outDir & "\" & vFile
        oDoc.Close SaveChanges:=False
        vFile = Dir
    Loop
    
    
End Sub
