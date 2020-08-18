from docx import Document
from docx.shared import Inches
from pymongo import MongoClient
import sys
import os
import io
import uuid
import boto3
from app.config import Config
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt,RGBColor,Cm
from docx.enum.text import WD_LINE_SPACING,WD_BREAK
from docx.oxml.shared import OxmlElement, qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.enum.dml import MSO_THEME_COLOR_INDEX
from zappa.asynchronous import task
from flask import send_file, jsonify
from docx.enum.table import WD_ALIGN_VERTICAL
from pymongo.collation import Collation
from docx.enum.table import WD_TABLE_ALIGNMENT

s3_client = boto3.client('s3')


def add_hyperlink1(paragraph,text, url):
    # This gets access to the document.xml.rels file and gets a new relation id value
    part = paragraph.part
    r_id = part.relate_to(url,RT.HYPERLINK, is_external=True)

    # Create the w:hyperlink tag and add needed values
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id, )

    # Create a w:r element and a new w:rPr element
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Join all the xml elements together add add the required text to the w:r element
    new_run.append(rPr)
    new_run.text =text
    hyperlink.append(new_run)

    # Create a new Run object and add the hyperlink into it
    r = paragraph.add_run ()
    r._r.append (hyperlink)

    # A workaround for the lack of a hyperlink style (doesn't go purple after using the link)
    # Delete this if using a template that has the hyperlink style in it
    r.font.color.theme_color = MSO_THEME_COLOR_INDEX.HYPERLINK
    r.font.underline = True
    r.font.bold=True 

    return hyperlink

def add_hyperlink(paragraph,text, url):
    # This gets access to the document.xml.rels file and gets a new relation id value
    part = paragraph.part
    r_id = part.relate_to(url,RT.HYPERLINK, is_external=True)

    # Create the w:hyperlink tag and add needed values
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id, )

    # Create a w:r element and a new w:rPr element
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Join all the xml elements together add add the required text to the w:r element
    new_run.append(rPr)
    new_run.text =text
    hyperlink.append(new_run)

    # Create a new Run object and add the hyperlink into it
    r = paragraph.add_run ()
    r._r.append (hyperlink)

    # A workaround for the lack of a hyperlink style (doesn't go purple after using the link)
    # Delete this if using a template that has the hyperlink style in it
    r.font.color.theme_color = MSO_THEME_COLOR_INDEX.HYPERLINK
    r.font.underline = True

    return hyperlink


def generateWordDocITPSOR(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):

    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)

    # Creation of the word document

    document = Document()

    # Implementing the "Two columns display" feature

    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')

    # Marging of the document

    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
   
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(12)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## SORENTRY ###############################################
    
    stlSorentry = document.styles.add_style('sorentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.bold = True
    
    pfSorentry = stlSorentry.paragraph_format

    # Line spacing
    
    pfSorentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
        
    ################## SORNORM ###############################################
    
    stlSornorm = document.styles.add_style('sornorm', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
   
    stlSornormFont=stlSornorm.font
    stlSornormFont.name = 'Arial'
    stlSornormFont.size = Pt(8)
    
    pfSornorm = stlSornorm.paragraph_format

    # Indentation
    
    pfSornorm.left_indent = Inches(0.50)

    # Line spacing
    
    pfSornorm.line_spacing_rule =  WD_LINE_SPACING.SINGLE

    ################## SORNOTE ###############################################
    
    stlSornote = document.styles.add_style('sornote', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSornoteFont=stlSornote.font
    stlSornoteFont.name = 'Arial'
    stlSornoteFont.size = Pt(8)    
    
    pfSornote = stlSornote.paragraph_format
    
    # Indentation
    
    pfSornote.left_indent = Inches(0.68)

    # Line spacing
    
    pfSornote.line_spacing_rule =  WD_LINE_SPACING.SINGLE
     
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Adding the sub Header to the document
    
    p1=header.add_paragraph(paramSubTitle, style='New sub Heading')
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph_format = p1.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(30)

    p3=header.add_paragraph("", style='New sub Heading')

    # Adding the Footer
    
    #footer = document.sections[0].footer
    #paragraph=footer.add_paragraph("No footer defined",style="New Heading")
    
    myRecords=setOfData

    for record in myRecords:
        
        try :
            sorentry= record['sorentry'].strip()
        except :
            sorentry=""
        
        try :
            if record['docSymbol'].strip()!="":
                docSymbol=record['docSymbol'].strip()
            else:
                docSymbol="Symbol not used."
        except :
            docSymbol="Symbol not used."

        try :
            sornorm=record['sornorm'].strip()
        except :
            sornorm=""

        try :
            sornote=record['sornote'].strip()
        except :
            sornote=""

        # Adding sorentry content
        p=document.add_paragraph(sorentry,style=stlSorentry)
        
        # Breaks management
        paragraph_format = p.paragraph_format
        paragraph_format.space_after = Pt(0)
        paragraph_format.space_before = Pt(0)

        
        # Breaks management
        paragraph_format.keep_together = True
        paragraph_format.keep_with_next = True
        
        # Force a tab
        p.add_run("\t")
        
        # Create the hyperlink for the document symbol
        if docSymbol!="Symbol not used." :
            add_hyperlink(p,docSymbol,Config.url_prefix+docSymbol)
        else:
            x=p.add_run("Symbol not used.")
            x.bold=False
            x.italic=True
            
            # Delete further space generated
            
            x_format = p.paragraph_format
            x_format.space_before = Pt(0)
            x_format.space_after = Pt(0)
        
        if sornorm!="" :
            # Adding sornorm content           
            p2=document.add_paragraph(sornorm,style=stlSornorm)
            
            # Breaks management
            paragraph_format = p2.paragraph_format
            paragraph_format.space_before = Pt(0)
            paragraph_format.space_after = Pt(0)

            # Breaks management
            paragraph_format.keep_together = True
            paragraph_format.keep_with_next = True

        if sornote!="" :
            # Adding sornote content  
            p3=document.add_paragraph(sornote,style=stlSornote)
            
            # Breaks management
            paragraph_format = p3.paragraph_format
            paragraph_format.space_before = Pt(0)

            # Breaks management
            paragraph_format.keep_together = True
            
        if sornote=="" and sornorm=="" :
            paragraph_format = p.paragraph_format
            paragraph_format.line_spacing =  1.5

    return document


def generateWordDocITPITSC(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)
    # Creation of the word document
    document = Document()

    # Two columns display
    
    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')
    
    # Marging of the document

    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)    
    
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## itshead ###############################################
    
    stlItsHead = document.styles.add_style('itshead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsHeadFont=stlItsHead.font
    stlItsHeadFont.name = 'Arial'
    stlItsHeadFont.size = Pt(9)
    stlItsHeadFont.bold = True
    
    pfItsHead = stlItsHead.paragraph_format

    # Line spacing
    
    pfItsHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    #pfItsHead.line_spacing =  1.5
    
    ################## itssubhead ###############################################
    
    stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsSubHeadFont=stlItssubHead.font
    stlItsSubHeadFont.name = 'Arial'
    stlItsSubHeadFont.size = Pt(8)
    stlItsSubHeadFont.bold = False
    
    pfItsSubHead = stlItssubHead.paragraph_format

    # Indentation
    
    pfItsSubHead.left_indent = Inches(0.20)
    
    # Line spacing
    
    pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    
    ################## itsentry ###############################################
    
    stlitsentry= document.styles.add_style('itsentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlitsentryFont=stlitsentry.font
    stlitsentryFont.name = 'Arial'
    stlitsentryFont.size = Pt(8)
    stlitsentryFont.bold = False
    
    
    pfstlitsentry = stlitsentry.paragraph_format

    # Indentation
    
    pfstlitsentry.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfstlitsentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## docsymbol ###############################################
    
    stlDocSymbol = document.styles.add_style('docsymbol', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlDocSymbolFont=stlDocSymbol.font
    stlDocSymbolFont.name = 'Arial'
    stlDocSymbolFont.size = Pt(8)
    stlDocSymbolFont.bold = False
    
    
    pfdocsymbol = stlDocSymbol.paragraph_format

    # Indentation
    
    pfdocsymbol.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfdocsymbol.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Adding the sub Header to the document
    
    p1=header.add_paragraph(mySubTitle.upper(), style='New sub Heading')
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Breaks management
    paragraph_format = p1.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(10)
    
    p3=header.add_paragraph("", style='New sub Heading')
    
    # Breaks management
    paragraph_format.keep_together = True
    paragraph_format.keep_with_next = True
    
    myRecords=setOfData

    for record in myRecords:
        
        try :
            itshead= record['itshead']
        except :
            itshead=""
        
        # Adding itshead content
        p=document.add_paragraph(itshead,style=stlItsHead)

        # Breaks management
        paragraph_format = p.paragraph_format
        # last update
        paragraph_format.space_after = Pt(1)
               
        # Breaks management
        paragraph_format.keep_together = True
        paragraph_format.keep_with_next = True
        
        subheading=record['subheading'] 
        
        for mysubhead in subheading:
                     
            itssubhead=mysubhead["itssubhead"]

            # Adding itssubhead content
            p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
            # Breaks management
            paragraph_format = p1.paragraph_format
            paragraph_format.space_after = Pt(0)
            
            # Breaks management
            paragraph_format.keep_together = True
            paragraph_format.keep_with_next = True
        
            itsentries=mysubhead["itsentries"]
            
            for itsentrie in itsentries :
                
                # retrieve itsentry value
                try:
                    itsentry=itsentrie["itsentry"]
                except : 
                    itsentry="Symbol not used."

                # Adding itssubhead content
                p2=document.add_paragraph(itsentry,style=stlitsentry)
                
                # Breaks management
                paragraph_format = p2.paragraph_format
                paragraph_format.space_after = Pt(0)
                
                # Breaks management
                paragraph_format.keep_together = True
                paragraph_format.keep_with_next = True

                # retrieve docsymbol value
                docsymbols=itsentrie["docsymbols"]
                
                # adding separator
                p2.add_run(" - ")

                # retrieving size of the list
                mySize=len(docsymbols)

                current=1

                for docsymbol in docsymbols:

                    add_hyperlink(p2,docsymbol,Config.url_prefix+docsymbol)
                    
                    # Breaks management
                    paragraph_format = p2.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    
                    # Breaks management
                    paragraph_format.keep_together = True

                    # Add the ';' and a space 
                    if mySize>1 and current<mySize:
                        p2.add_run("; ")

                    current+=1
                
        # Force a new line before next heading
        p2.add_run("\n")

    return document

  
def generateWordDocITPITSP(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)

    # Creation of the word document
    document = Document()

    # Two columns display
    
    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')
    
    # Marging of the document

    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)    
    
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## itshead ###############################################
    
    stlItsHead = document.styles.add_style('itshead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsHeadFont=stlItsHead.font
    stlItsHeadFont.name = 'Arial'
    stlItsHeadFont.size = Pt(9)
    stlItsHeadFont.bold = True
    
    pfItsHead = stlItsHead.paragraph_format

    # Line spacing
    
    pfItsHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    #pfItsHead.line_spacing =  1.5
    
    ################## itssubhead ###############################################
    
    stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsSubHeadFont=stlItssubHead.font
    stlItsSubHeadFont.name = 'Arial'
    stlItsSubHeadFont.size = Pt(8)
    stlItsSubHeadFont.bold = False
    
    pfItsSubHead = stlItssubHead.paragraph_format

    # Indentation
    
    pfItsSubHead.left_indent = Inches(0.20)
    
    # Line spacing
    
    pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    
    ################## itsentry ###############################################
    
    stlitsentry= document.styles.add_style('itsentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlitsentryFont=stlitsentry.font
    stlitsentryFont.name = 'Arial'
    stlitsentryFont.size = Pt(8)
    stlitsentryFont.bold = False
    
    
    pfstlitsentry = stlitsentry.paragraph_format

    # Indentation
    
    pfstlitsentry.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfstlitsentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## docsymbol ###############################################
    
    stlDocSymbol = document.styles.add_style('docsymbol', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlDocSymbolFont=stlDocSymbol.font
    stlDocSymbolFont.name = 'Arial'
    stlDocSymbolFont.size = Pt(8)
    stlDocSymbolFont.bold = False
    
    
    pfdocsymbol = stlDocSymbol.paragraph_format

    # Indentation
    
    pfdocsymbol.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfdocsymbol.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Adding the sub Header to the document
    
    p1=header.add_paragraph(mySubTitle.upper(), style='New sub Heading')
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Breaks management
    paragraph_format = p1.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(10)
    
    p3=header.add_paragraph("", style='New sub Heading')
    
    # Breaks management
    paragraph_format.keep_together = True
    paragraph_format.keep_with_next = True
    
    myRecords=setOfData

    for record in myRecords:
        
        try :
            itshead= record['itshead']
        except :
            itshead=""
        
        # Adding itshead content
        p=document.add_paragraph(itshead,style=stlItsHead)

        # Breaks management
        paragraph_format = p.paragraph_format
        paragraph_format.space_after = Pt(1)
               
        # Breaks management
        paragraph_format.keep_together = True
        paragraph_format.keep_with_next = True
        
        subheading=record['subheading'] 
        
        for mysubhead in subheading:
                     
            itssubhead=mysubhead["itssubhead"]

            # Adding itssubhead content
            p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
            # Breaks management
            paragraph_format = p1.paragraph_format
            paragraph_format.space_after = Pt(0)
            
            # Breaks management
            paragraph_format.keep_together = True
            paragraph_format.keep_with_next = True
        
            itsentries=mysubhead["itsentries"]
            
            for itsentrie in itsentries :
                
                # retrieve itsentry value
                try:
                    itsentry=itsentrie["itsentry"]
                except : 
                    itsentry=" "

                # Adding itssubhead content
                p2=document.add_paragraph(itsentry,style=stlitsentry)
                
                # Breaks management
                paragraph_format = p2.paragraph_format
                paragraph_format.space_after = Pt(0)
                
                # Breaks management
                paragraph_format.keep_together = True
                paragraph_format.keep_with_next = True

                # retrieve docsymbol value
                docsymbols=itsentrie["docsymbols"]
                
                # retrieving size of the list
                mySize=len(docsymbols)

                current=1

                for docsymbol in sorted(docsymbols):

                    add_hyperlink(p2,docsymbol,Config.url_prefix+docsymbol)
                    
                    # Breaks management
                    paragraph_format = p2.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    
                    # Breaks management
                    paragraph_format.keep_together = True

                    # Add the ';' and a space 
                    if mySize>1 and current<mySize:
                        p2.add_run("; ")

                    current+=1
                
        # Force a new line before next heading
        p2.add_run("\n")
  
    return document    


def generateWordDocITPITSS(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):

    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)

    # Creation of the word document
    document = Document()

    # Two columns display
    
    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')
    
    # Marging of the document

    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)    
    
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## itshead ###############################################
    
    stlItsHead = document.styles.add_style('itshead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsHeadFont=stlItsHead.font
    stlItsHeadFont.name = 'Arial'
    stlItsHeadFont.size = Pt(9)
    stlItsHeadFont.bold = True
    
    pfItsHead = stlItsHead.paragraph_format

    # Line spacing
    
    pfItsHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    #pfItsHead.line_spacing =  1.5
    
    ################## itssubhead ###############################################
    
    stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsSubHeadFont=stlItssubHead.font
    stlItsSubHeadFont.name = 'Arial'
    stlItsSubHeadFont.size = Pt(8)
    stlItsSubHeadFont.bold = False
    
    pfItsSubHead = stlItssubHead.paragraph_format

    # Indentation
    
    pfItsSubHead.left_indent = Inches(0.20)
    
    # Line spacing
    
    pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    
    ################## itsentry ###############################################
    
    stlitsentry= document.styles.add_style('itsentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlitsentryFont=stlitsentry.font
    stlitsentryFont.name = 'Arial'
    stlitsentryFont.size = Pt(8)
    stlitsentryFont.bold = False
    
    
    pfstlitsentry = stlitsentry.paragraph_format

    # Indentation
    
    pfstlitsentry.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfstlitsentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## docsymbol ###############################################
    
    stlDocSymbol = document.styles.add_style('docsymbol', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlDocSymbolFont=stlDocSymbol.font
    stlDocSymbolFont.name = 'Arial'
    stlDocSymbolFont.size = Pt(8)
    stlDocSymbolFont.bold = False
    
    
    pfdocsymbol = stlDocSymbol.paragraph_format

    # Indentation
    
    pfdocsymbol.left_indent = Inches(0.40)
    
    # Line spacing
    
    pfdocsymbol.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Adding the sub Header to the document
    
    p1=header.add_paragraph(mySubTitle.upper(), style='New sub Heading')
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Breaks management
    paragraph_format = p1.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(10)
    
    p3=header.add_paragraph("", style='New sub Heading')
    
    # Breaks management
    paragraph_format.keep_together = True
    paragraph_format.keep_with_next = True
    
    myRecords=setOfData

    for record in myRecords:
        
        try :
            itshead= record['itshead']
        except :
            itshead=""
        
        # Adding itshead content
        p=document.add_paragraph(itshead,style=stlItsHead)

        # Breaks management
        paragraph_format = p.paragraph_format
        paragraph_format.space_after = Pt(1)
               
        # Breaks management
        paragraph_format.keep_together = True
        paragraph_format.keep_with_next = True
        
        subheading=record['subheading'] 
        
        for mysubhead in subheading:
                     
            itssubhead=mysubhead["itssubhead"]

            # Adding itssubhead content
            p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
            # Breaks management
            paragraph_format = p1.paragraph_format
            paragraph_format.space_after = Pt(0)
            
            # Breaks management
            paragraph_format.keep_together = True
            paragraph_format.keep_with_next = True
        
            itsentries=mysubhead["itsentries"]
            
            for itsentrie in itsentries :
                
                # retrieve itsentry value
                try:
                    itsentry=itsentrie["itsentry"]
                except : 
                    itsentry="Symbol not used."

                # Adding itssubhead content
                p2=document.add_paragraph(itsentry,style=stlitsentry)
                
                # Breaks management
                paragraph_format = p2.paragraph_format
                paragraph_format.space_after = Pt(0)
                
                # Breaks management
                paragraph_format.keep_together = True
                paragraph_format.keep_with_next = True

                # retrieve docsymbol value
                docsymbols=itsentrie["docsymbols"]
                
                # adding separator
                p2.add_run(" - ")

                # retrieving size of the list
                mySize=len(docsymbols)

                current=1

                for docsymbol in sorted(docsymbols):

                    add_hyperlink(p2,docsymbol,Config.url_prefix+docsymbol)
                    
                    # Breaks management
                    paragraph_format = p2.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    
                    # Breaks management
                    paragraph_format.keep_together = True

                    # Add the ';' and a space 
                    if mySize>1 and current<mySize:
                        p2.add_run("; ")

                    current+=1
                
        # Force a new line before next heading
        p2.add_run("\n")
 
    return document  

def generateWordDocITPRES(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Function to keep the header visible for the table

    def set_repeat_table_header(row):

        tr = row._tr
        trPr = tr.get_or_add_trPr()
        tblHeader = OxmlElement('w:tblHeader')
        tblHeader.set(qn('w:val'), "true")
        trPr.append(tblHeader)
        return row

    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle1=paramSubTitle
    #setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sortkey1",1)
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sortkey1",1).collation(Collation(locale='en',numericOrdering=True))
    
    # Creation of the word document
    document = Document()
    
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(12)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(12)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)

    ################## FIRST LINE ###############################################
    
    first_line = styles.add_style('first line', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font settings
    
    font = first_line.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.italic=True
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## SPECIAL ###############################################
    
    special = styles.add_style('special', WD_STYLE_TYPE.PARAGRAPH)
    pf = special.paragraph_format
    pf.left_indent = Inches(0.40)
    # Font settings
    font = special.font
    font.underline=True
    
    
    ################## TABLE CONTENT ###############################################
    
    tableContent_style = styles.add_style('tableContent', WD_STYLE_TYPE.PARAGRAPH)
    tableContent_style.base_style = styles['Normal']
    
    # Font settings
    
    font = tableContent_style.font
    font.name = 'Arial'
    font.size = Pt(8)

    
    # Hanging indent    

    pf = tableContent_style.paragraph_format
    #pf.first_line_indent = Inches(-0.02)
    
    pf.first_line_indent = Inches(-0.06)

    ################## TABLE CONTENT 1 ###############################################
    
    tableContent_style1 = styles.add_style('tableContent1', WD_STYLE_TYPE.PARAGRAPH)
    tableContent_style1.base_style = styles['Normal']
    
    # Font settings
    
    font = tableContent_style1.font
    font.name = 'Arial'
    font.size = Pt(8)

    
    # Hanging indent    

    pf1 = tableContent_style1.paragraph_format
    pf1.left_indent = Pt(10)
    pf1.space_before = Pt(1)
    
    #pf.first_line_indent = Inches(10)

    ################## WRITING THE DOCUMENT ###############################################
    
    # Header Generation
    
    if (bodysession[0] in ["A","E"]):
        #p=header.add_paragraph(mySubTitle1.upper(),style='New Heading')
        p=header.add_paragraph(myTitle.upper(),style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    else : 
        p=header.add_paragraph(myTitle.upper(), style='New Heading')
        #p=header.add_paragraph(myTitle, style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
        # Adding the sub Header to the document
    
        p=header.add_paragraph(mySubTitle1, style='New sub Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
 
    # First line generation

    paragraph_format = p.paragraph_format
    paragraph_format.space_after = Pt(20)
    paragraph_format.left_indent=Cm(0.508)

    p=document.add_paragraph("Vote reads Yes-No-Abstain",style='first line')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph_format = p.paragraph_format
    paragraph_format.left_indent=Inches(0.35)

    # Definition of the column names
    myRecords=setOfData

    if (bodysession[0] in ["A","E"]):

        # creation of the table
        table = document.add_table(rows=1, cols=5)

        table.alignment = WD_TABLE_ALIGNMENT.LEFT
        #table.allow_autofit=True

        # set the header visible
        set_repeat_table_header(table.rows[0])

        # Retrieve the first line
        hdr_cells = table.rows[0].cells

        firstTitle= myRecords[0]["docsymbol"].split("/")
        baseUrl1=firstTitle[0] + "/" + firstTitle[1] + "/" + firstTitle[2] + "/" 
        firstlineValue= myRecords[0]["meeting"].split(".")
        baseUrl2="("+firstlineValue[0]+".-)"
        
        run = hdr_cells[0].paragraphs[0].add_run(baseUrl1)
        run.underline=True
        
        run = hdr_cells[1].paragraphs[0].add_run('Title')
        tc = hdr_cells[1]._tc
        tcPr = tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        start = OxmlElement('w:start')
        
        tcMar.set(qn('w:w'), "0")
        tcMar.set(qn('w:type'),"dxa")
              
        tcMar.append(start)
        tcPr.append(tcMar)
        run.underline=True     
        
        hdr_cells[2].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        #run = hdr_cells[2].paragraphs[0].add_run('Meeting / Date' +  "               " +baseUrl2)
        run = hdr_cells[2].paragraphs[0].add_run('Meeting / Date')
        run.underline=True
        run1=hdr_cells[2].paragraphs[0].add_run("               " +baseUrl2)
        
        hdr_cells[3].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        run = hdr_cells[3].paragraphs[0].add_run('A.I. No.')
        run.underline=True
        
        hdr_cells[4].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        run = hdr_cells[4].paragraphs[0].add_run('Vote')
        run.underline=True
        

        # writing the others lines

        for record in myRecords:
            firstTitle=""
            firstlineValue=""
            firstTitle= record["docsymbol"].split("/")
            firstlineValue= record["meeting"].split(".")
            row_cells = table.add_row().cells

            add_hyperlink(row_cells[0].paragraphs[0],firstTitle[3],Config.url_prefix+firstTitle[0]+"/"+firstTitle[1]+"/"+firstTitle[2]+"/"+firstTitle[3])
            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[1].text=record["title"]
            row_cells[1].paragraphs[0].style="tableContent"   
            add_hyperlink(row_cells[2].paragraphs[0],firstlineValue[1],Config.url_prefix+firstlineValue[0]+"."+firstlineValue[1])
            
            row_cells[2].paragraphs[0].add_run( " / " + record["votedate"])
            row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            ############################################
            
            row_cells[3].text=record["ainumber"]
            row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            ############################################
            
            row_cells[4].text=record["vote"]
            row_cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER


        # Definition of the size of the column
        #  #widths = (Inches(0.73), Inches(3.30), Inches(1.05), Inches(0.61), Inches(1.10)) second version
        widths = (Inches(0.43), Inches(5.00), Inches(1.25), Inches(1.0), Inches(1.10))
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = width

    else :

        # creation of the table
        table = document.add_table(rows=1, cols=4)

        table.alignment = WD_TABLE_ALIGNMENT.LEFT
        #table.allow_autofit=True

        # set the header visible
        set_repeat_table_header(table.rows[0])

        # Retrieve the first line
        hdr_cells = table.rows[0].cells

        firstTitle= myRecords[0]["docsymbol"].split("/")
        baseUrl1=firstTitle[0] + "/" + firstTitle[1] + "/"
        firstlineValue= (myRecords[0]["meeting"].split("."))[0].split("/")

        baseUrl2="  ("+firstlineValue[0]+"/"+ firstlineValue[2] +".-)"

        hdr_cells[0].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        run = hdr_cells[0].paragraphs[0].add_run(baseUrl1)
        run.underline=True
        
        run = hdr_cells[1].paragraphs[0].add_run('Subject')
        tc2 = hdr_cells[1]._tc
        tcPr2 = tc2.get_or_add_tcPr()
        tcMar2 = OxmlElement('w:tcMar')
        start2 = OxmlElement('w:start')
        
        tcMar2.set(qn('w:w'), "0")
        tcMar2.set(qn('w:type'),"dxa")
              
        tcMar2.append(start2)
        tcPr2.append(tcMar2)
        run.underline=True


        hdr_cells[2].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        run = hdr_cells[2].paragraphs[0].add_run('Meeting / Date, '+myRecords[0]["voteyear"] )
        run.underline=True
        run1=hdr_cells[2].paragraphs[0].add_run(" "+baseUrl2)

        hdr_cells[3].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        run = hdr_cells[3].paragraphs[0].add_run('Vote')
        run.underline=True
       

        # writing the others lines

        for record in myRecords:
            firstTitle=""
            firstlineValue=""
            firstTitle= record["docsymbol"].split("/")
            firstlineValue= record["meeting"].split(".")
            firstlineValuePlus=firstlineValue[0].split("/")
            row_cells = table.add_row().cells

            add_hyperlink(row_cells[0].paragraphs[0],firstTitle[2],Config.url_prefix+firstTitle[0]+"/"+firstTitle[1]+"/"+firstTitle[2]) 
            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[1].paragraphs[0].text=record["subject"].upper()
            
            ########
            tc2 = row_cells[1]._tc
            tcPr2 = tc2.get_or_add_tcPr()
            tcMar2 = OxmlElement('w:tcMar')
            start2 = OxmlElement('w:start')
            
            tcMar2.set(qn('w:w'), "0")
            tcMar2.set(qn('w:type'),"dxa")
                
            tcMar2.append(start2)
            tcPr2.append(tcMar2)

            ########
            
            paragraph_format = row_cells[1].paragraphs[0].paragraph_format
            paragraph_format.space_before = Pt(0)
            paragraph_format.space_after = Pt(0)
            row_cells[1].add_paragraph(record["subjectsubtitle"],style="tableContent1")
            
            row_cells[2].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
            add_hyperlink(row_cells[2].paragraphs[0],firstlineValue[1],Config.url_prefix+firstlineValuePlus[0]+"/"+ firstlineValuePlus[2]+ "."+firstlineValue[1])
            row_cells[2].paragraphs[0].add_run( " / " + record["votedate"])

            row_cells[3].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
            #row_cells[3].text=record["vote"]
            row_cells[3].paragraphs[0].text=record["vote"]

        # Definition of the size of the column

        # widths = (Inches(1.20), Inches(4.06), Inches(1.2), Inches(1.10), Inches(0.8))
        # widths = (Inches(1.20), Inches(5.06), Inches(1.2),Inches(0.8))
        # widths = (Inches(0.8), Inches(4.06), Inches(1.2),Inches(0.75)
        widths = (Inches(1.3), Inches(5.06), Inches(1.7),Inches(0.75))
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = width

    # Definition of the font

    for row in table.rows:
        for cell in row.cells:
            paragraphs = cell.paragraphs
            for paragraph in paragraphs:
                # Adding styling
                for run in paragraph.runs:
                    font = run.font
                    font.name="Arial"
                    font.size= Pt(7)

    # Save the document
    return document  

def generateWordDocITPSUBJ(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # # Setting some Variables

    # myMongoURI=Config.connect_string
    # myClient = MongoClient(myMongoURI)
    # myDatabase=myClient.undlFiles
    # myCollection=myDatabase['itp_sample_output_copy']
    # myTitle=paramTitle
    # mySubTitle=paramSubTitle
    # setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)
    # lCol=True
    # rCol=False
    # toTalLineNumber = 48
    # currentLineNumber=1
    # lColMaxHead=46
    # rColMaxHead=40
    # lColMax = 61
    # rColMax = 57

    # # Creation of the word document
    # document = Document()

    # # Two columns display
    
    # section = document.sections[0]
    # sectPr = section._sectPr
    # cols = sectPr.xpath('./w:cols')[0]
    # cols.set(qn('w:num'),'2')
    
    # # Marging of the document

    # section.top_margin = Cm(1.54)
    # # section.bottom_margin = Cm(2.54)
    # section.left_margin = Cm(2.54)
    # section.right_margin = Cm(2.54)    
    

    
    # ################## HEADER ###############################################
    
    # styles = document.styles
    # new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    # new_heading_style.base_style = styles['Heading 1']
    
    # # Font settings
    
    # font = new_heading_style.font
    # font.name = 'Arial'
    # font.size = Pt(8)
    # font.bold = False
    # font.color.rgb = RGBColor(0, 0, 0)
    
    # # Adding the header to the document
    
    # header=document.sections[0].header

    # pfnew_heading_style = new_heading_style.paragraph_format
    # pfnew_heading_style.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    # ################## SUBHEADER ###############################################
    
    # new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    # new_sub_heading_style.base_style = styles['Heading 1']
    
    # # Font settings
    
    # font = new_sub_heading_style.font
    # font.name = 'Arial'
    # font.size = Pt(8)
    # font.bold = False
    # font.color.rgb = RGBColor(0, 0, 0)
    
    # ################## itshead ###############################################
    
    # stlItsHead = document.styles.add_style('itshead', WD_STYLE_TYPE.PARAGRAPH)
    
    # # Font name
    
    # stlItsHeadFont=stlItsHead.font
    # stlItsHeadFont.name = 'Arial'
    # stlItsHeadFont.size = Pt(9)
    # stlItsHeadFont.bold = True
    
    # pfItsHead = stlItsHead.paragraph_format

    # # Line spacing
    
    # pfItsHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    

    
    # ################## itssubhead ###############################################
    
    # stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # # Font name
    
    # stlItsSubHeadFont=stlItssubHead.font
    # stlItsSubHeadFont.name = 'Arial'
    # stlItsSubHeadFont.size = Pt(9)
    # stlItsSubHeadFont.bold = True
    # stlItsSubHeadFont.underline = True
    
    # pfItsSubHead = stlItssubHead.paragraph_format

    # # Indentation
    
    # pfItsSubHead.left_indent = Inches(0)
    
    # # Line spacing
    
    # pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    
    # ################## itsentry ###############################################
    
    # stlitsentry= document.styles.add_style('itsentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # # Font name
    
    # stlitsentryFont=stlitsentry.font
    # stlitsentryFont.name = 'Arial'
    # stlitsentryFont.size = Pt(8)
    # stlitsentryFont.bold = False
    
    
    # pfstlitsentry = stlitsentry.paragraph_format

    # # Indentation
    
    # pfstlitsentry.left_indent = Inches(0.15)
    
    # # Line spacing
    
    # pfstlitsentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    # ################## note ###############################################
    
    # stlNote = document.styles.add_style('note', WD_STYLE_TYPE.PARAGRAPH)
    
    # # Font name
    
    # stlNoteFont=stlNote.font
    # stlNoteFont.name = 'Arial'
    # stlNoteFont.size = Pt(8)
    
    # pfNote = stlNote.paragraph_format

    # # Indentation
    
    # #pfNote.left_indent = Inches(0.40)
    # pfNote.first_line_indent = Cm(0.90)
    
    # # Line spacing
    
    # pfNote.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    # ################## WRITING THE DOCUMENT ###############################################
    
    # # Adding the Header to the document
    
    # p=header.add_paragraph(myTitle.upper(), style='New Heading')
    # p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # # Adding the sub Header to the document
    
    # p1=header.add_paragraph(mySubTitle.upper(), style='New sub Heading')
    # p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # p1.add_run("\n")
    # p1.add_run("\n")

    # # Breaks management
    # paragraph_format = p1.paragraph_format
    # paragraph_format.space_before = Pt(0)
    # paragraph_format.space_after = Pt(10)
    # paragraph_format.keep_together = True
    # paragraph_format.keep_with_next = True
    
    # myRecords=setOfData

    # for record in myRecords:

    #     try :
    #         itshead= record['head']
    #     except :
    #         itshead=""
        
    #     # Adding itshead content
    #     print(f"The length of the header is  : {len(itshead)} ")
    #     myLastItsHead=itshead + " (continued)"
        
    #     # we are inside the first column
    #     if (lCol==True and rCol==False):
    #         numberLine=(round(len(itshead)/lColMaxHead)+1)
    #         if (currentLineNumber+numberLine)<=toTalLineNumber:
    #             currentLineNumber+=numberLine
    #             print(myLastItsHead)
    #             p=document.add_paragraph(itshead,style=stlItsHead)
                
    #         else: #  (currentLineNumber+numberLine)>toTalLineNumber
                
    #             # Assign the boolean values of the cols
    #             lCol,rCol=(False,True)
                
    #             # Insertion of the break point
                
                
    #             # Write the head title + continued
                
                
            
    #     # we are inside the second column        
    #     if (lCol==False and rCol==True):
    #          pass     
                  
                  
                  
                  

        

    #     # Breaks management
    #     paragraph_format = p.paragraph_format
    #     paragraph_format.space_after = Pt(5)
    #     paragraph_format.space_before = Pt(0)
    #     paragraph_format.keep_together = True
    #     paragraph_format.keep_with_next = True
        
    #     subheading=record['subheading'] 

    #     for mysubhead in subheading:

    #         itssubhead=mysubhead["subhead"]
    #         print(f"The length of the subheader is  : {len(itssubhead)} ")
    #         print(f"In theory the number of the lines needed to display is : {round(len(itssubhead)/61) + 1} ")

    #         # Adding itssubhead content
    #         p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
    #         # Breaks management
    #         paragraph_format = p1.paragraph_format
    #         paragraph_format.space_after = Pt(6)
    #         paragraph_format.space_before = Pt(0)
    #         paragraph_format.keep_together = True
    #         paragraph_format.keep_with_next = True
        
            
    #         itsentries=mysubhead["entries"]
            
    #         for entry in itsentries:
       
    #             #Adding itssubhead content
    #             p2=document.add_paragraph(" ",style=stlitsentry)
    #             p2.paragraph_format.first_line_indent = Pt(-10)

    #             # We have some separators between docsymbole
    #             try:
    #                 result=entry["docsymbol"].find(" ")
    #                 if result > 0 :
    #                     myEntry=entry["docsymbol"].split(" ")
    #                     add_hyperlink1(p2,myEntry[0],Config.url_prefix+myEntry[0])
                        
    #                     p2.add_run(" ")
    #                     p2.add_run(myEntry[1])

                    
    #                 else :
                        
    #                     add_hyperlink1(p2,str(entry["docsymbol"]),Config.url_prefix+entry["docsymbol"])          
                
    #             except:
    #                 pass

    #             if entry["note"]!="":
    #                 p2.add_run(" ")
    #                 print(f"The length of the note is  : {len(entry['entry'])} ")
    #                 print(f"In theory the number of the lines needed to display is : {round(len(entry['entry'])/61) + 1} ")
    #                 p2.add_run(entry["entry"])
                    
    #                 #Breaks management
    #                 paragraph_format = p2.paragraph_format
    #                 paragraph_format.space_after = Pt(0)
    #                 paragraph_format.space_before = Pt(0)
    #                 # paragraph_format.keep_together = True
    #                 # paragraph_format.keep_with_next = True
                
    #                 #Adding itssubhead content
    #                 print(f"The length of the note is  : {len(entry['note'])} ")
    #                 print(f"In theory the number of the lines needed to display is : {round(len(entry['note'])/61) + 1} ")
    #                 p3=document.add_paragraph(entry["note"],style=stlNote)
                    
                    
    #                 #Breaks management
    #                 paragraph_format = p3.paragraph_format
    #                 paragraph_format.space_after = Pt(3)
    #                 paragraph_format.space_before = Pt(0)
    #                 # paragraph_format.keep_together = True
    #                 # paragraph_format.keep_with_next = True
                
    #             else:
    #                 print(f"The length of the note is  : {len(entry['entry'])} ")
    #                 print(f"In theory the number of the lines needed to display is : {round(len(entry['entry'])/61) + 1} ")
    #                 p2.add_run(" ")
    #                 p2.add_run(entry["entry"])
                    
    #                 #Breaks management
    #                 paragraph_format = p2.paragraph_format
    #                 #paragraph_format.space_after = Pt(5)
    #                 paragraph_format.space_after = Pt(3)
    #                 paragraph_format.space_before = Pt(0)
    #                 paragraph_format.keep_together = True
    #                 paragraph_format.keep_with_next = True

    # return document    

     
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    #setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)

    # Creation of the word document
    document = Document()

    # Two columns display
    
    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')
    
    # Marging of the document

    section.top_margin = Cm(1.54)
    # section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)    
    

    
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header

    pfnew_heading_style = new_heading_style.paragraph_format
    pfnew_heading_style.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## SUBHEADER ###############################################
    
    new_sub_heading_style = styles.add_style('New sub Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.bold = False
    font.color.rgb = RGBColor(0, 0, 0)
    
    ################## itshead ###############################################
    
    stlItsHead = document.styles.add_style('itshead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsHeadFont=stlItsHead.font
    stlItsHeadFont.name = 'Arial'
    stlItsHeadFont.size = Pt(9)
    stlItsHeadFont.bold = True
    
    pfItsHead = stlItsHead.paragraph_format

    # Line spacing
    
    pfItsHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    

    
    ################## itssubhead ###############################################
    
    stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsSubHeadFont=stlItssubHead.font
    stlItsSubHeadFont.name = 'Arial'
    stlItsSubHeadFont.size = Pt(9)
    stlItsSubHeadFont.bold = True
    stlItsSubHeadFont.underline = True
    
    pfItsSubHead = stlItssubHead.paragraph_format

    # Indentation
    
    pfItsSubHead.left_indent = Inches(0)
    
    # Line spacing
    
    pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    
    ################## itsentry ###############################################
    
    stlitsentry= document.styles.add_style('itsentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlitsentryFont=stlitsentry.font
    stlitsentryFont.name = 'Arial'
    stlitsentryFont.size = Pt(8)
    stlitsentryFont.bold = False
    
    
    pfstlitsentry = stlitsentry.paragraph_format

    # Indentation
    
    pfstlitsentry.left_indent = Inches(0.15)
    
    # Line spacing
    
    pfstlitsentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## note ###############################################
    
    stlNote = document.styles.add_style('note', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlNoteFont=stlNote.font
    stlNoteFont.name = 'Arial'
    stlNoteFont.size = Pt(8)
    
    pfNote = stlNote.paragraph_format

    # Indentation
    
    #pfNote.left_indent = Inches(0.40)
    pfNote.first_line_indent = Cm(0.90)
    
    # Line spacing
    
    pfNote.line_spacing_rule =  WD_LINE_SPACING.SINGLE
    
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Adding the sub Header to the document
    
    p1=header.add_paragraph(mySubTitle.upper(), style='New sub Heading')
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run("\n")
    p1.add_run("\n")

    # Breaks management
    paragraph_format = p1.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(10)
    paragraph_format.keep_together = True
    paragraph_format.keep_with_next = True
    
    myRecords=setOfData

    for record in myRecords:

        try :
            itshead= record['head']
        except :
            itshead=""
        
        # Adding itshead content
        p=document.add_paragraph(itshead,style=stlItsHead)

        # Breaks management
        paragraph_format = p.paragraph_format
        paragraph_format.space_after = Pt(5)
        paragraph_format.space_before = Pt(0)
        paragraph_format.keep_together = True
        paragraph_format.keep_with_next = True
        
        subheading=record['subheading'] 

        for mysubhead in subheading:

            itssubhead=mysubhead["subhead"]

            # Adding itssubhead content
            p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
            # Breaks management
            paragraph_format = p1.paragraph_format
            paragraph_format.space_after = Pt(6)
            paragraph_format.space_before = Pt(0)
            paragraph_format.keep_together = True
            paragraph_format.keep_with_next = True
        
            
            itsentries=mysubhead["entries"]
            
            for entry in itsentries:
       
                #Adding itssubhead content
                p2=document.add_paragraph(" ",style=stlitsentry)
                p2.paragraph_format.first_line_indent = Pt(-10)

                # We have some separators between docsymbole
                try:
                    result=entry["docsymbol"].find(" ")
                    if result > 0 :
                        myEntry=entry["docsymbol"].split(" ")
                        add_hyperlink1(p2,myEntry[0],Config.url_prefix+myEntry[0])
                        
                        p2.add_run(" ")
                        p2.add_run(myEntry[1])

                    
                    else :
                        
                        add_hyperlink1(p2,str(entry["docsymbol"]),Config.url_prefix+entry["docsymbol"])          
                
                except:
                    pass
                



                if entry["note"]!="":
                    p2.add_run(" ")
                    p2.add_run(entry["entry"])
                    
                    #Breaks management
                    paragraph_format = p2.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    paragraph_format.space_before = Pt(0)
                    # paragraph_format.keep_together = True
                    # paragraph_format.keep_with_next = True
                
                    #Adding itssubhead content
                    p3=document.add_paragraph(entry["note"],style=stlNote)
                    
                    #Breaks management
                    paragraph_format = p3.paragraph_format
                    paragraph_format.space_after = Pt(3)
                    paragraph_format.space_before = Pt(0)
                    # paragraph_format.keep_together = True
                    # paragraph_format.keep_with_next = True
                
                else:
                    p2.add_run(" ")
                    p2.add_run(entry["entry"])
                    
                    #Breaks management
                    paragraph_format = p2.paragraph_format
                    #paragraph_format.space_after = Pt(5)
                    paragraph_format.space_after = Pt(3)
                    paragraph_format.space_before = Pt(0)
                    paragraph_format.keep_together = True
                    paragraph_format.keep_with_next = True

    return document    



def generateWordDocITPDSL(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection}).sort("sort",1)

    # Creation of the word document

    document = Document()

    # Implementing the "Two columns display" feature

    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')

    # Marging of the document

    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
   
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(12)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Adding the header to the document
    
    header=document.sections[0].header
   
   ################## SORENTRY ###############################################
    
    stlSorentry = document.styles.add_style('sorentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.bold = True
    
    pfSorentry = stlSorentry.paragraph_format

    # Line spacing
    
    pfSorentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
        
    ################## SORNORM ###############################################
    
    stlSornorm = document.styles.add_style('sornorm', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
   
    stlSornormFont=stlSornorm.font
    stlSornormFont.name = 'Arial'
    stlSornormFont.size = Pt(8)
    stlSornormFont.bold = True
    
    pfSornorm = stlSornorm.paragraph_format

    # Line spacing
    
    pfSornorm.line_spacing_rule =  WD_LINE_SPACING.SINGLE

    ################## SORNOTE ###############################################
    
    stlSornote = document.styles.add_style('sornote', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSornoteFont=stlSornote.font
    stlSornoteFont.name = 'Arial'
    stlSornoteFont.size = Pt(8)    
    
    pfSornote = stlSornote.paragraph_format

    # Line spacing
    
    pfSornote.line_spacing_rule =  WD_LINE_SPACING.SINGLE
     
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("\n")
    p.add_run("\n")
 
    myRecords=setOfData

    for record in myRecords:
        
        p1=document.add_paragraph(record["committee"],style="sorentry")       
        
        mySeries = record["series"]
        
        for serie in mySeries:
        
            p2=document.add_paragraph(serie["series"],style="sornorm")
            
            p2.add_run("\n")
            
            myDocSymbols=serie["docsymbols"]
            
            p3=document.add_paragraph(style="sornote")
            
            print(myDocSymbols)
            
            for doc in myDocSymbols:
                
                p3.add_run(doc)
                p3.add_run("\n")
                    

    return document

    