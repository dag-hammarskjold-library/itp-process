from __future__ import division
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
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_LINE_SPACING
import itertools
import math


s3_client = boto3.client('s3')


global globaltotalLines
global totalLinesAvailableOne
global totalLinesAvailableTwo
global titleTotalLength
global subtitleTotalLength
global entryTotalLength
global actualColumn
global lastTitle

globaltotalLines=60
totalLinesAvailableOne=60
totalLinesAvailableTwo=60
titleTotalLength=48
subtitleTotalLength=37
entryTotalLength=44
actualColumn="One"
lastTitle=""

def create_element(name):
    return OxmlElement(name)


def create_attribute(element, name, value):
    element.set(qn(name), value)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    page_run = paragraph.add_run()
    t1 = create_element('w:t')
    create_attribute(t1, 'xml:space', 'preserve')
    t1.text = '- '
    page_run._r.append(t1)

    font = page_run.font
    font.name="Arial"
    font.size= Pt(8)

    page_num_run = paragraph.add_run()

    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')

    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"

    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')

    page_num_run._r.append(fldChar1)
    page_num_run._r.append(instrText)
    page_num_run._r.append(fldChar2)
    
    font = page_num_run.font
    font.name="Arial"
    font.size= Pt(8)

    of_run = paragraph.add_run()
    t2 = create_element('w:t')
    create_attribute(t2, 'xml:space', 'preserve')
    t2.text = ' -'
    of_run._r.append(t2)

    font = of_run.font
    font.name="Arial"
    font.size= Pt(8)
    

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
        print(record)
        try :
            sorentry= record['sorentry'].strip()
        except :
            sorentry=""
        
        try :
            if record['docsymbol'].strip()!="":
                docSymbol=record['docsymbol'].strip()
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
            if (bodysession[0] in ["E"]):
                recup=docSymbol.split(" ")
                add_hyperlink(p,docSymbol,Config.url_prefix+recup[0])
            else:
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

    add_page_number(document.sections[0].footer.paragraphs[0])
    return document

def generateWordDocITPITSC(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})
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
    
    #pfstlitsentry.left_indent = Inches(0.40)
    pfstlitsentry.first_line_indent = Inches(-0.20)
    pfstlitsentry.left_indent = Inches(0.50)
    
    
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
        paragraph_format.space_after = Pt(3)
               
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
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})

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
    
    pfstlitsentry.first_line_indent = Inches(-0.20)
    pfstlitsentry.left_indent = Inches(0.50)
    
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
        paragraph_format.space_after = Pt(3)
               
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
  
    add_page_number(document.sections[0].footer.paragraphs[0])
    return document    


def generateWordDocITPITSS(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):

    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    mySubTitle=paramSubTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})

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
    
    pfstlitsentry.first_line_indent = Inches(-0.20)
    pfstlitsentry.left_indent = Inches(0.50)
    
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
        paragraph_format.space_after = Pt(3)
               
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
    
    add_page_number(document.sections[0].footer.paragraphs[0])
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
    add_page_number(document.sections[0].footer.paragraphs[0])
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
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})

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
    
    pfNote.left_indent = Inches(0.05)

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
        # paragraph_format.keep_together = True
        # paragraph_format.keep_with_next = True
        
        subheading=record['subheading'] 

        for mysubhead in subheading:

            itssubhead=mysubhead["subhead"]

            # Adding itssubhead content
            p1=document.add_paragraph(itssubhead,style=stlItssubHead)
            
            # Breaks management
            paragraph_format = p1.paragraph_format
            paragraph_format.space_after = Pt(6)
            paragraph_format.space_before = Pt(0)
            # paragraph_format.keep_together = True
            # paragraph_format.keep_with_next = True
        
            
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
                    paragraph_format.space_after = Pt(7)
                    paragraph_format.space_before = Pt(0)
                    # paragraph_format.keep_together = True
                    # paragraph_format.keep_with_next = True
   
                
                else:
                    p2.add_run(" ")
                    p2.add_run(entry["entry"])
                    
                    #Breaks management
                    paragraph_format = p2.paragraph_format
                    #paragraph_format.space_after = Pt(5)
                    paragraph_format.space_after = Pt(7)
                    paragraph_format.space_before = Pt(0)
                    # paragraph_format.keep_together = True
                    # paragraph_format.keep_with_next = True

    add_page_number(document.sections[0].footer.paragraphs[0])
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



    # # Marging of the document

    # section.top_margin = Cm(2.54)
    # section.bottom_margin = Cm(2.54)
    # section.left_margin = Cm(2.54)
    # section.right_margin = Cm(2.54)
   
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
    #stlSorentryFont.size = Pt(10)
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
    
    myRecords=setOfData
    x=0

    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("\n")
    p.add_run("\n")

    section = document.sections[0]
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'1')

    if (bodysession[0]=="A"):
        p=document.add_paragraph("NOTE :   Languages of corrigenda are indicated only when corrigenda are not issued in all six official languages.Documents issued as Supplements to the Official Records of the General Assembly, Seventy-second Session are so indicated. Information regarding documents bearing the double symbol A/  and S/  can be found in the Supplements to the Official Records of the Security Council. The information provided below is current as of the date this Index is submitted for publication.",style="sornote")
    
    if (bodysession[0]=="E"):
        p=document.add_paragraph("NOTE: Languages of corrigenda are indicated only when corrigenda are not issued in all six languages. Documents issued as Supplements to the Official Records of the Economic and Social Council, 2018 are also indicated. The information provided below is current as of the date this Index is submitted for publication.",style="sornote")
   
    if (bodysession[0]=="S"):
        p=document.add_paragraph("NOTE: Languages of corrigenda are indicated only when corrigenda are not issued in all six official languages. The information provided below is current as of the date this Index is submitted for publication.",style="sornote")
    
    p.add_run("\n")

    p=document.add_paragraph(myRecords[0]["committee"],style="sorentry")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    section = document.add_section(WD_SECTION.CONTINUOUS)
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'),'2')

    for record in myRecords:
        
        if x>0:
            p1=document.add_paragraph(record["committee"],style="sorentry")  
            p1.alignment = WD_ALIGN_PARAGRAPH.CENTER    
 
        x=x+1
        mySeries = record["series"]
        
        for serie in mySeries:
        
            p2=document.add_paragraph(serie["series"],style="sornorm")
            
            #p2.add_run("\n")
            
            myDocSymbols=serie["docsymbols"]
            
            p3=document.add_paragraph(style="sornote")
            
            for doc in myDocSymbols:
                
                p3.add_run(doc)
                p3.add_run("\n")
                    
    add_page_number(document.sections[0].footer.paragraphs[0])
    return document

def generateWordDocITPMEET(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):

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
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})
    setOfData1=myCollection.find({'bodysession': bodysession,'section': paramSection})

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

    ################## itssubhead ###############################################
    
    stlItssubHead = document.styles.add_style('itssubhead', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlItsSubHeadFont=stlItssubHead.font
    stlItsSubHeadFont.name = 'Arial'
    stlItsSubHeadFont.size = Pt(8)

    pfItsSubHead = stlItssubHead.paragraph_format

    # Indentation
    
    pfItsSubHead.left_indent = Inches(0)
    
    # Line spacing
    
    pfItsSubHead.line_spacing_rule =  WD_LINE_SPACING.SINGLE
   
   ################## stylemeeting ###############################################
    
    stlSorentry = document.styles.add_style('stylemeeting', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    
    pfSorentry = stlSorentry.paragraph_format

    ################## styletableheader ###############################################
    
    stlSorentry = document.styles.add_style('styletableheader', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    
    pfSorentry = stlSorentry.paragraph_format
    pfSorentry.space_after = Pt(10)
     
    ################## WRITING THE DOCUMENT ###############################################
    
    if (bodysession[0]=="S"):

        # Adding the Header to the document

        section = document.sections[0]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')[0]
        cols.set(qn('w:num'),'3')

        datas=setOfData

        p=header.add_paragraph(myTitle.upper(), style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")
        
        p=header.add_paragraph("(Symbol: " + datas[0]["symbol"] +")", style='itssubhead')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")
        p.add_run("\n")

        # creation of the table
        table = document.add_table(rows=1, cols=2)

        table.allow_autofit=True

        #table.rows.height_rule = WD_ROW_HEIGHT_RULE.AUTO

        table.alignment = WD_TABLE_ALIGNMENT.LEFT

        # set the header visible
        set_repeat_table_header(table.rows[0])

        # Retrieve the first line
        hdr_cells = table.rows[0].cells

        myRun=hdr_cells[0].paragraphs[0].add_run('Meeting')
        myRun.underline=True

        myRun=hdr_cells[1].paragraphs[0].add_run('Date, '+datas[0]["years"][0]["year"])
        hdr_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        myRun.underline=True

        myRun=hdr_cells[1].paragraphs[0].add_run('\n')

        for data in datas:
            records=data["years"]
            for record in records:
                meetings=record["meetings"]
                for meeting in meetings:
                    row_cells = table.add_row().cells
                    row_cells[0].paragraphs[0].text=meeting["meetingnum"]
                    row_cells[1].paragraphs[0].text=meeting["meetingdate"]
                    row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER 
    
        # Definition of the size of the column

        widths = (Inches(2), Inches(1.5))
        for row in table.rows:
            for idx,width in enumerate(widths):
                row.cells[idx].width = width

        # Definition of the font

        for row in table.rows:
            for cell in row.cells:
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    # Adding styling
                    for run in paragraph.runs:
                        font = run.font
                        font.name="Arial"
                        font.size= Pt(8)
        
        add_page_number(document.sections[0].footer.paragraphs[0])
        return document
    

    if (bodysession[0]=="E"):
        
        datas=setOfData
        datas1=setOfData1

        p=header.add_paragraph(myTitle.upper(), style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")
        p.add_run("\n")
        
        p=header.add_paragraph("(Symbol: " + datas[0]["symbol"] +")", style='itssubhead')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")

        ###########################################################################################
        # Process
        ###########################################################################################
        
        # 0- Settings

        section = document.sections[0]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')[0]
        cols.set(qn('w:num'),'3')

        nbRecords=0
        nbYears=0
        nbMeetings=0

        # 1- Count the number of records

        for data in datas:
            nbRecords=nbRecords+1
            for year in data["years"]:
                nbYears=nbYears+1
                for meeting in year["meetings"]:
                    nbMeetings=nbMeetings+1

        # 2- Define the number of records per cols
        nbMeeting=1
        nbrRecPerCol0= round(nbMeetings / 3)
        nbrRecPerCol1= round(nbMeetings / 3)

        nbrRecPerCol2= round(nbMeetings / 3)
        nbrRecPerCol3= nbMeetings - (nbrRecPerCol1+nbrRecPerCol2)


        # 3- Define a closure feature

        # 4- Display the record after check of the date a new date should call the closure function

        startGroup=False

        for data1 in datas1:
            for year1 in data1["years"]:

                if startGroup==True:

                    hdr_cells = table.rows[nbMeeting].cells
                    hdr_cells[1].text=" "
                    nbMeeting=nbMeeting+1

                    hdr_cells = table.rows[nbMeeting].cells
                    hdr_cells[1].text="Date, "+ year1["year"]
                    paragraphs = hdr_cells[1].paragraphs
                    for paragraph in paragraphs:
                        for run in paragraph.runs:
                            font = run.font
                            font.underline=True
                    nbMeeting=nbMeeting+1

                    hdr_cells = table.rows[nbMeeting].cells
                    hdr_cells[1].text=" "
                    nbMeeting=nbMeeting+1

                    table.add_row()
                    table.add_row()
                    table.add_row()

                    nbrRecPerCol1=nbrRecPerCol1+3

                for meeting1 in year1["meetings"]:

                    if (nbMeeting<=nbrRecPerCol1):

                        if nbMeeting==1:

                            p=document.add_paragraph()
                            run = p.add_run()
                            
                            table = document.add_table(rows=nbrRecPerCol1+1,cols=2)
                        
                            # set the header visible
                            set_repeat_table_header(table.rows[0])

                            # Retrieve the first line
                            hdr_cells = table.rows[0].cells
                            myRun=hdr_cells[0].paragraphs[0].add_run('Meeting')
                            myRun.underline=True
                            myRun=hdr_cells[1].paragraphs[0].add_run('Date, '+year1["year"])
                            hdr_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                            myRun.underline=True
                            myRun=hdr_cells[1].paragraphs[0].add_run('\n')
                            #nbMeeting=nbMeeting+1
                            hdr_cells = table.rows[nbMeeting].cells
                            hdr_cells[0].text=meeting1["meetingnum"]
                            hdr_cells[1].text=meeting1["meetingdate"]
                            
                        else :

                            # fill the cell of the table
                            hdr_cells = table.rows[nbMeeting].cells
                            hdr_cells[0].text=meeting1["meetingnum"]
                            hdr_cells[1].text=meeting1["meetingdate"]


                    # if (nbMeeting>nbrRecPerCol1 and nbMeeting<=2*nbrRecPerCol2):
                    if (nbMeeting>nbrRecPerCol1):


                        if nbMeeting==nbrRecPerCol1+1:


                            # column break
                            p=document.add_paragraph()
                            run = p.add_run()
                            myBreak = run.add_break(WD_BREAK.COLUMN)
                            table = document.add_table(rows=nbrRecPerCol1+1,cols=2)
                        
                            # set the header visible
                            set_repeat_table_header(table.rows[0])

                            # Retrieve the first line
                            hdr_cells = table.rows[0].cells
                            myRun=hdr_cells[0].paragraphs[0].add_run('Meeting')
                            myRun.underline=True
                            myRun=hdr_cells[1].paragraphs[0].add_run('Date, '+year1["year"])
                            hdr_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                            myRun.underline=True
                            myRun=hdr_cells[1].paragraphs[0].add_run('\n')

                            nbMeeting=1
                            nbrRecPerCol1=nbrRecPerCol0
                            hdr_cells = table.rows[nbMeeting].cells
                            hdr_cells[0].text=meeting1["meetingnum"]
                            hdr_cells[1].text=meeting1["meetingdate"]
                            
                        else :

                            # fill the cell of the table
                            hdr_cells = table.rows[nbMeeting].cells
                            hdr_cells[0].text=meeting1["meetingnum"]
                            hdr_cells[1].text=meeting1["meetingdate"]

                    
                    nbMeeting=nbMeeting+1
                
                startGroup=True


        # Apply the font
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    paragraphs = cell.paragraphs
                    cell.width = Inches(0.7)
                    for paragraph in paragraphs:
                        # Adding styling
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        paragraph_format = paragraph.paragraph_format
                        paragraph_format.space_after = Pt(0)
                        for run in paragraph.runs:
                            font = run.font
                            font.name="Arial"
                            font.size= Pt(8)

        add_page_number(document.sections[0].footer.paragraphs[0])
        return document

    if (bodysession[0]=="A"):
        
        # retrieving the data
        datas=setOfData
        datas1=setOfData1

        # definition of the header
        p=header.add_paragraph(myTitle.upper(), style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")
        p.add_run("\n")
        p.add_run("\n")

        ###########################################################################################
        # Process
        ###########################################################################################
        
        # 0- Settings

        section = document.sections[0]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')[0]
        cols.set(qn('w:num'),'3')

        for data1 in datas1:
            
            nbrRecPerCol1=0
            nbrRecPerCol2=0
            nbrRecPerCol3=0
            myCommittee1=data1["committee1"]
            myCommittee2=data1["committee2"]
            mySymbol=data1["symbol"]
            nbMeeting=0

            startGroup=False

            for year in data1["years"]:
                nbMeeting+=len(year["meetings"])

            if nbMeeting>9 :

                nbrRecPerCol1= round(nbMeeting / 3)
                nbrRecPerCol2= round(nbMeeting / 3)
                nbrRecPerCol3= nbMeeting - (nbrRecPerCol1+nbrRecPerCol2)

                ######################################################################

                table = document.add_table(rows=nbrRecPerCol1+1,cols=2)

                # Retrieve the first line
                for year in data1["years"]:
                    hdr_cells = table.rows[0].cells
                    myRun=hdr_cells[0].paragraphs[0].add_run('Meeting')
                    myRun.underline=True
                    myRun=hdr_cells[1].paragraphs[0].add_run('Date,'+year["year"])
                    hdr_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                    myRun.underline=True

                    myRow=0
                    for meeting in year["meetings"]:

                        if myRow<nbrRecPerCol1:
                            if myRow==0:

                                # column break
                                p=document.add_paragraph()
                                run = p.add_run()
                                myBreak = run.add_break(WD_BREAK.COLUMN)

                                # myRow should be reseted
                                myRow=1

                                # create the table
                                table = document.add_table(rows=nbrRecPerCol1+1,cols=2)

                            else:
                                hdr_cells = table.rows[myRow].cells
                                hdr_cells[0].text=meeting["meetingnum"]
                                hdr_cells[1].text=meeting["meetingdate"]

                        if myRow>=nbrRecPerCol1 and 2*nbrRecPerCol1:
                            if myRow==nbrRecPerCol1:

                                # column break
                                p=document.add_paragraph()
                                run = p.add_run()
                                myBreak = run.add_break(WD_BREAK.COLUMN)

                                # myRow should be reseted
                                myRow=1

                                # create the table
                                table = document.add_table(rows=nbrRecPerCol1+1,cols=2)

                            else:

                                hdr_cells = table.rows[myRow].cells
                                hdr_cells[0].text=meeting["meetingnum"]
                                hdr_cells[1].text=meeting["meetingdate"]

                        if myRow>2*nbrRecPerCol1:
                            if myRow==2*nbrRecPerCol1:

                                # column break
                                p=document.add_paragraph()
                                run = p.add_run()
                                myBreak = run.add_break(WD_BREAK.COLUMN)

                                # myRow should be reseted
                                myRow=1

                                # create the table
                                table = document.add_table(rows=nbrRecPerCol3+1,cols=2)

                            else:
                                hdr_cells = table.rows[myRow].cells
                                hdr_cells[0].text=meeting["meetingnum"]
                                hdr_cells[1].text=meeting["meetingdate"]

                        myRow+=1

                ######################################################################

            else :

                nbrRecPerCol1= nbMeeting
                
                # build and align the table with one column
                p=document.add_paragraph()
                run = p.add_run("\n")
                run = p.add_run("\n")
                run = p.add_run("\n")

                table = document.add_table(rows=nbrRecPerCol1+1,cols=2)

                # Retrieve the first line
                for year in data1["years"]:
                    hdr_cells = table.rows[0].cells
                    myRun=hdr_cells[0].paragraphs[0].add_run('Meeting')
                    myRun.underline=True
                    myRun=hdr_cells[1].paragraphs[0].add_run('Date,'+year["year"])
                    hdr_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                    myRun.underline=True

                    myRow=1
                    for meeting in year["meetings"]:

                        if myRow<=nbMeeting:
                            hdr_cells = table.rows[myRow].cells
                            hdr_cells[0].text=meeting["meetingnum"]
                            hdr_cells[1].text=meeting["meetingdate"]

                        myRow+=1



    





        # # Apply the font
        # for table in document.tables:
        #     for row in table.rows:
        #         for cell in row.cells:
        #             paragraphs = cell.paragraphs
        #             for paragraph in paragraphs:
        #                 # Adding styling
        #                 paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        #                 paragraph_format = paragraph.paragraph_format
        #                 paragraph_format.space_after = Pt(0)
        #                 for run in paragraph.runs:
        #                     font = run.font
        #                     font.name="Arial"
        #                     font.size= Pt(8)


        return document


def generateWordDocITPAGE(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})

    # Creation of the word document

    document = Document()
   
    ################## HEADER ###############################################
    
    styles = document.styles
    new_heading_style = styles.add_style('New Heading', WD_STYLE_TYPE.PARAGRAPH)
    # new_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    
    font = new_heading_style.font
    font.name = 'Arial'
    font.size = Pt(12)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)

    # Adding the header to the document
    
    header=document.sections[0].header
    

    ################## SORTITLE ###############################################
    
    stlSorentry = document.styles.add_style('sortitle', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.bold = True
    
    pfSorentry = stlSorentry.paragraph_format
    pfSorentry.left_indent = Inches(0.80)

    # Line spacing
    
    pfSorentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE

    ################## SORNOTETITLE ###############################################
    
    sornotetitle = document.styles.add_style('sornotetitle', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=sornotetitle.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)

    ################## see ###############################################
    
    see = document.styles.add_style('see3', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=see.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.italic=True

    pformat=see.paragraph_format
    pformat.space_after=Pt(5)
    pformat.left_indent=Cm(2)
    pformat.first_line_indent=Inches(-0.58)

    ################## see ###############################################
    
    see = document.styles.add_style('see4', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=see.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.italic=True

    ################## see ###############################################
    
    see = document.styles.add_style('see', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=see.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.italic=True

    ################## data ###############################################
    
    data = document.styles.add_style('data', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=data.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.italic=False

    ################## NOTE ###############################################
    
    stlSorentry = document.styles.add_style('note', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    stlSorentryFont.italic = True
    
    pfSorentry = stlSorentry.paragraph_format
    pfSorentry.left_indent = Inches(1.39)

    # Line spacing
    
    pfSorentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE
   
   ################## SORENTRY ###############################################
    
    stlSorentry = document.styles.add_style('sorentry', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSorentryFont=stlSorentry.font
    stlSorentryFont.name = 'Arial'
    stlSorentryFont.size = Pt(8)
    
    pfSorentry = stlSorentry.paragraph_format

    # Line spacing
    
    pfSorentry.line_spacing_rule =  WD_LINE_SPACING.SINGLE

    ################## see2 ###############################################
    
    stlSee = document.styles.add_style('see2', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSeeFont=stlSee.font
    stlSeeFont.italic=True
    stlSeeFont.name = 'Arial'
    stlSeeFont.size = Pt(8)

    pformat=stlSee.paragraph_format
    pformat.space_after=Pt(5)
    pformat.left_indent=Cm(1.52)
    pformat.first_line_indent=Inches(-0.58)
 

    ################## title2 ###############################################
    
    stlTitle2 = document.styles.add_style('title2', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name and size
    
    stlTitle2Font=stlTitle2.font
    stlTitle2Font.name = 'Arial'
    stlTitle2Font.size = Pt(8)

    # others formatting
    
    pformat=stlTitle2.paragraph_format
    pformat.space_before=Pt(0)
    pformat.space_after=Pt(1)
    pformat.left_indent=Cm(1.52)
    pformat.first_line_indent=Inches(-0.30)

    ################## subagenda2 ###############################################
    
    stlSubagenda2 = document.styles.add_style('subagenda2', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name and size
    
    stlSubagenda2Font=stlSubagenda2.font
    stlSubagenda2Font.name = 'Arial'
    stlSubagenda2Font.size = Pt(8)

    # others formatting
    
    pformat=stlSubagenda2.paragraph_format
    pformat.space_before=Pt(0)
    pformat.space_after=Pt(2)
    pformat.left_indent=Cm(2.29)
    pformat.first_line_indent=Inches(-0.58)

    ################## mysubject ###############################################
    
    stlMysubject2 = document.styles.add_style('mysubject2', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name and size
    
    stlMysubject2Font=stlMysubject2.font
    stlMysubject2Font.name = 'Arial'
    stlMysubject2Font.size = Pt(8)

    # others formatting
    
    pformat=stlMysubject2.paragraph_format
    pformat.space_before=Pt(0)
    pformat.space_after=Pt(5)
    pformat.left_indent=Cm(2.50)
    pformat.first_line_indent=Inches(-0.68)
     
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document

    ########### GENERAL ASSEMBLY ##########

    if (bodysession[0]=="A"):

        myRecords=setOfData
        preventDoubleValue=""

        for record in myRecords:  
      
            # Display management
            
            if record["heading"]=="AGENDA":

                p=header.add_paragraph(myTitle.upper(), style='New Heading')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                section = document.sections[0]
                sectPr = section._sectPr
                cols = sectPr.xpath('./w:cols')[0]
                cols.set(qn('w:num'),'2')

                # Selection of the agenda object
                for myAgenda in record["agendas"]:

                    # Selection of the agendanum value
                    myAgendaNum=myAgenda["agendanum"]

                    # Selection of the text object
                    alreadyDisplayText=False
                    alreadyDisplayNum=False
                    alreadyDisplaySee=False
                    alreadyDisplaySeeAlso=False
                    alreadyDisplaySeeAlso1=False
                    saveTitle=""
                    seeAlso1=False
                    for myText in myAgenda["text"]:

                        # Selection of the subagenda value
                        if myText["subagenda"]:
                            mySubAgenda=myText["subagenda"].strip()

                        # Selection of the agendatext value
                        for myAgendaText in myText["agendatext"]:

                            # Selection of the title value

                            if myAgendaText["title"]!="":
                                myTitle=myAgendaText["title"].strip()

                            if alreadyDisplayNum==False:
                                if len(myAgendaNum)==1 :
                                    p=document.add_paragraph(myAgendaNum+"."+"       ",style="title2")
                                else:
                                    p=document.add_paragraph(myAgendaNum+"."+"     ",style="title2")    
                                run=p.add_run(myTitle)
                                alreadyDisplayNum=True
                                
                            else:
                                ##

                                if len(myAgenda["text"])!=1:
                                    if saveTitle!=myTitle:
                                        p=document.add_paragraph("         ("+  mySubAgenda    +")     ",style="subagenda2")   
                                        run=p.add_run(myTitle)
                                        saveTitle=myTitle
                                        seeAlso1=True
                            
                            # Selection of the subject value
                            alreadyDisplayMultipleSee=False
                            alreadyDisplayMultipleb=False
                            index=0
                            for mySubject in myAgendaText["subjects"]:
                                if mySubject:
                                    if alreadyDisplaySee==False:
                                        if len(myAgenda["text"])==1:
                                            p=document.add_paragraph("\t"+"See:  ",style='see2') 
                                            run=p.add_run(mySubject.strip())
                                            run.font.italic=False
                                            alreadyDisplaySee=True
 
                                        else:
                                            # here see + () header under the header level
                                            if myText["subagenda"]!="":
                                                p=document.add_paragraph("                            See:  ",style="see2")
                                                run=p.add_run(mySubject.strip()) 
                                                run.font.italic=False
                                                alreadyDisplaySee=True

                                            
                                            if myText["subagenda"]=="":
                                                p=document.add_paragraph("                   See:  ",style="see2")
                                                run=p.add_run(mySubject.strip()) 
                                                run.font.italic=False
                                                alreadyDisplaySee=True                                           
                                            
                                    
                                    else:
                                        
                                        # normal scenario
                                        if len(myAgenda["text"])==1 and myText["agendatext"][0]["subjects"][0]=="":
                                            ####### yls
                                            p=document.add_paragraph("                   "+mySubject.strip(),style="mysubject2")  
                                            alreadyDisplayMultipleb=True
                                                
                                        if len(myAgenda["text"])!=1 :
                                            # here see + () contents inside the contents
                                            if preventDoubleValue!=mySubject:
                                                if alreadyDisplayMultipleSee==False:
                                                    p=document.add_paragraph("                            See:   ",style="see2")
                                                    run=p.add_run(mySubject.strip()) # 17 spaces
                                                    run.font.italic=False
                                                    alreadyDisplayMultipleSee=True
                                                    preventDoubleValue=mySubject

                                                else:
                                                    p=document.add_paragraph("                             "+mySubject.strip(),style="mysubject2")
                                                preventDoubleValue=mySubject

                                        if len(myText["agendatext"])==2 and myText["agendatext"][0]["title"]!="" and myText["agendatext"][1]["title"]=="" and myText["subagenda"]=="" and myText["agendatext"][0]["subjects"][0]!="":
                                            if alreadyDisplaySeeAlso==False:
                                                p=document.add_paragraph("                   See also:   ",style="see2")
                                                run=p.add_run(mySubject.strip()) # 17 spaces
                                                run.font.italic=False 
                                                alreadyDisplaySeeAlso=True
                                            else:
                                                p=document.add_paragraph("                                     ",style="see2")
                                                run=p.add_run(mySubject.strip()) # 17 spaces
                                                run.font.italic=False 
 
                                            continue

                                        if len(myText["agendatext"])==2 and myText["agendatext"][0]["title"]!="" and myText["agendatext"][1]["title"]=="" and myText["subagenda"]!="" and myText["agendatext"][0]["subjects"][0]!="":
                                            if alreadyDisplaySeeAlso==False:
                                                p=document.add_paragraph("                            See also:   ",style="see2")
                                                run=p.add_run(myText["agendatext"][1]["subjects"][0].strip()) # 17 spaces
                                                run.font.italic=False 
                                                alreadyDisplaySeeAlso=True
                                                preventDoubleValue=myText["agendatext"][1]["subjects"][0]
 
                                            continue

                                else : # no subject
                                    if len(myAgenda["text"])==1:
                                        #run=p.add_run("\n")
                                        p.paragraph_format.space_after = Pt(5)
                                    #pass 

        sections = document.sections
        for section in sections:
            section.top_margin = Cm(1)
            section.bottom_margin = Cm(1)
            section.left_margin = Cm(1)
            section.right_margin = Cm(1)

    # add_page_number(document.sections[0].footer.paragraphs[0])
    # return document


    ### SECURITY COUNCIL ##########

    if (bodysession[0]=="S"):

        myRecords=setOfData

        p=document.add_paragraph(myTitle.upper(), style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        section = document.sections[0]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')[0]
        cols.set(qn('w:num'),'1')
        
        p1=document.add_paragraph("", style='sornotetitle')
        p1.add_run("The Council's practice is to adopt at each meeting, on the basis of a provisional agenda circulated in advance, the agenda for that meeting. At subsequent meetings an item may appear in its original form or with the addition of such sub-items as the Council may decide to include. Once included in the agenda, an item remains on the list of matters of which the Council is seized, until the Council agrees to its removal.")
        p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY_LOW

        p2=document.add_paragraph("", style='sornotetitle')
        p2.add_run('The agenda as adopted for each meeting in 2018 will be found in the Official Records of the Security Council, Seventy-third Year (S/PV.8152-8439). A list of weekly summary statements of matters of which the Security Council is seized, and on the stage reached in their consideration, submitted by the Secretary-General under rule 11 of the provisional rules of procedure of the Security Council, appears in the Subject index under the heading "UN. SECURITY COUNCIL (2018)–AGENDA".')
        p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY_LOW

        p3=document.add_paragraph("", style='sornotetitle')
        p3.add_run('Listed below are the matters considered by, or brought to the attention of the Council during 2018. They are arranged alphabetically by the subject headings under which related documents are to be found in the Subject index.')
        p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY_LOW
        p3.add_run("\n")
    
        p.add_run("\n")

        p=document.add_paragraph("       "+myRecords[0]["heading"],style="sortitle")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p=document.add_paragraph('NOTE: Subject headings under which documentation related to agenda items is listed \n    in the Subject index appear in capital letters following the title of the item.',style='note')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p.add_run("\n")
        p.add_run("\n")

        p=document.add_paragraph('',style='sorentry')
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        for record in myRecords[0]["agendas"]:

            p.add_run("[To be completed manually]")
            p.add_run("\n")
            run=p.add_run("See    ")
            run.font.italic=True
            run=p.add_run(record["subject"])
            run.font.italic=False
            p.add_run("\n")
            p.add_run("\n")

            
        ### SECOND RECORD ##########
        p=document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # run = p.add_run()
        # run.add_break(WD_BREAK.PAGE)

        p=document.add_paragraph(myRecords[1]["heading"],style="sortitle")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p=document.add_paragraph('NOTE: These items were not discussed by the Council',style='note')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p.add_run("\n")
        p.add_run("\n")

        p=document.add_paragraph('',style='sorentry')
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        for record in myRecords[1]["agendas"]:

            p.add_run("[To be completed manually]")
            p.add_run("\n")
            run=p.add_run("See    ")
            run.font.italic=True
            run=p.add_run(record["subject"])
            run.font.italic=False
            p.add_run("\n")
            p.add_run("\n")

        # add_page_number(document.sections[0].footer.paragraphs[0])
        # return document

    ########## ECOSOC ##########

    if (bodysession[0]=="E"):

        myRecords=setOfData
        preventDoubleValue=""

        for record in myRecords:  
      
            # Display management
            
            if record["heading"]=="AGENDA":

                p=header.add_paragraph(myTitle.upper(), style='New Heading')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                section = document.sections[0]
                sectPr = section._sectPr
                cols = sectPr.xpath('./w:cols')[0]
                cols.set(qn('w:num'),'1')

                # Selection of the agenda object
                for myAgenda in record["agendas"]:

                    # Selection of the agendanum value
                    myAgendaNum=myAgenda["agendanum"]

                    # Selection of the text object
                    alreadyDisplayText=False
                    alreadyDisplayNum=False
                    alreadyDisplaySee=False
                    alreadyDisplaySeeAlso=False
                    alreadyDisplaySeeAlso1=False
                    saveTitle=""
                    seeAlso1=False
                    for myText in myAgenda["text"]:

                        # Selection of the subagenda value
                        if myText["subagenda"]:
                            mySubAgenda=myText["subagenda"].strip()

                        # Selection of the agendatext value
                        for myAgendaText in myText["agendatext"]:

                            # Selection of the title value

                            if myAgendaText["title"]!="":
                                myTitle=myAgendaText["title"].strip()

                            if alreadyDisplayNum==False:
                                if int(myAgendaNum)<10 :
                                    p=document.add_paragraph(myAgendaNum+"."+"       ",style="title2")
                                else:
                                    p=document.add_paragraph(myAgendaNum+"."+"     ",style="title2")    
                                run=p.add_run(myTitle)
                                alreadyDisplayNum=True
                                
                            else:
                                ##

                                if len(myAgenda["text"])!=1:
                                    if saveTitle!=myTitle:
                                        p=document.add_paragraph("         ("+  mySubAgenda    +")     ",style="subagenda2")   
                                        run=p.add_run(myTitle)
                                        saveTitle=myTitle
                                        seeAlso1=True
                            
                            # Selection of the subject value
                            alreadyDisplayMultipleSee=False
                            alreadyDisplayMultipleb=False
                            index=0
                            for mySubject in myAgendaText["subjects"]:
                                if mySubject:
                                    if alreadyDisplaySee==False:
                                        if len(myAgenda["text"])==1:
                                            p=document.add_paragraph("\t"+"See:  ",style='see2') 
                                            run=p.add_run(mySubject.strip())
                                            run.font.italic=False
                                            alreadyDisplaySee=True
 
                                        else:
                                            # here see + () header under the header level
                                            if myText["subagenda"]!="":
                                                p=document.add_paragraph("                            See:  ",style="see2")
                                                run=p.add_run(mySubject.strip()) 
                                                run.font.italic=False
                                                alreadyDisplaySee=True

                                            
                                            if myText["subagenda"]=="":
                                                p=document.add_paragraph("                   See:  ",style="see2")
                                                run=p.add_run(mySubject.strip()) 
                                                run.font.italic=False
                                                alreadyDisplaySee=True                                           
                                            
                                    
                                    else:
                                        
                                        # normal scenario
                                        if len(myAgenda["text"])==1 and myText["agendatext"][0]["subjects"][0]=="":
                                            ####### yls
                                            p=document.add_paragraph("                   "+mySubject.strip(),style="mysubject2")  
                                            alreadyDisplayMultipleb=True
                                                
                                        if len(myAgenda["text"])!=1 :
                                            # here see + () contents inside the contents
                                            if preventDoubleValue!=mySubject:
                                                if alreadyDisplayMultipleSee==False:
                                                    p=document.add_paragraph("                            See:   ",style="see2")
                                                    run=p.add_run(mySubject.strip()) # 17 spaces
                                                    run.font.italic=False
                                                    alreadyDisplayMultipleSee=True
                                                    preventDoubleValue=mySubject

                                                else:
                                                    p=document.add_paragraph("                             "+mySubject.strip(),style="mysubject2")
                                                preventDoubleValue=mySubject

                                        if len(myText["agendatext"])==2 and myText["agendatext"][0]["title"]!="" and myText["agendatext"][1]["title"]=="" and myText["subagenda"]=="" and myText["agendatext"][0]["subjects"][0]!="":
                                            if alreadyDisplaySeeAlso==False:
                                                p=document.add_paragraph("                   See also:   ",style="see2")
                                                run=p.add_run(mySubject.strip()) # 17 spaces
                                                run.font.italic=False 
                                                alreadyDisplaySeeAlso=True
                                            else:
                                                p=document.add_paragraph("                                     ",style="see2")
                                                run=p.add_run(mySubject.strip()) # 17 spaces
                                                run.font.italic=False 
 
                                            continue

                                        if len(myText["agendatext"])==2 and myText["agendatext"][0]["title"]!="" and myText["agendatext"][1]["title"]=="" and myText["subagenda"]!="" and myText["agendatext"][0]["subjects"][0]!="":
                                            if alreadyDisplaySeeAlso==False:
                                                p=document.add_paragraph("                            See also:   ",style="see2")
                                                run=p.add_run(myText["agendatext"][1]["subjects"][0].strip()) # 17 spaces
                                                run.font.italic=False 
                                                alreadyDisplaySeeAlso=True
                                                preventDoubleValue=myText["agendatext"][1]["subjects"][0]
 
                                            continue

                                else : # no subject
                                    if len(myAgenda["text"])==1:
                                        #run=p.add_run("\n")
                                        p.paragraph_format.space_after = Pt(5)
                                    #pass

            if record["heading"]=="OTHER MATTERS INCLUDED IN THE INDEX":   

                myBreak = p.add_run().add_break(WD_BREAK.PAGE)

                paragraph = header.paragraphs[0]

                # Choosing the top most sectin of the page 
                section = document.sections[0] 
                
                # Selecting the header 
                header = section.header 
                
                # Selecting the paragraph already present in 
                # the header section 
                header_para = header.paragraphs[0] 

                # Selection of the agenda object
                for myAgenda in record["agendas"]:

                    for myText in myAgenda["text"]:

                        for myAgendaText in myText["agendatext"]:

                            for mySubject in myAgendaText["subjects"]:

                                p=document.add_paragraph(mySubject,style="title2")    

        sections = document.sections
        for section in sections:
            section.top_margin = Cm(1)
            section.bottom_margin = Cm(1)
            section.left_margin = Cm(1)
            section.right_margin = Cm(1)

    add_page_number(document.sections[0].footer.paragraphs[0])
    return document


def generateWordDocITPVOT(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    myTitle=paramTitle
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})
    setOfData1=myCollection.find({'bodysession': bodysession,'section': paramSection})
    setOfData2=myCollection.find({'bodysession': bodysession,'section': paramSection})

    # Creation of the word document

    document = Document()

    # Adding the header to the document
    
    header=document.sections[0].header
    header.orientation=WD_ORIENT.LANDSCAPE

    section = document.sections[0]
    section.orientation=WD_ORIENT.LANDSCAPE
    new_height = section.page_width
    section.page_width = section.page_height
    section.page_height = new_height
   
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

    pfNew_heading_style = new_heading_style.paragraph_format
    pfNew_heading_style.alignment=WD_ALIGN_PARAGRAPH.CENTER
    

    ################## SUBTITLE ###############################################
    
    stlSubtitle = document.styles.add_style('subtitle', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlSubtitleFont=stlSubtitle.font
    stlSubtitleFont.name = 'Arial'
    stlSubtitleFont.size = Pt(8)
    
    pfSubtitle = stlSubtitle.paragraph_format
    pfSubtitle.left_indent = Inches(0.80)
    pfSubtitle.alignment=WD_ALIGN_PARAGRAPH.CENTER

    # Line spacing
    
    pfSubtitle.line_spacing_rule =  WD_LINE_SPACING.SINGLE

    ################## CONTENT ###############################################
    
    stlContent = document.styles.add_style('content', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font name
    
    stlContentFont=stlContent.font
    stlContentFont.name = 'Arial'
    stlContentFont.size = Pt(8)
    
    pfContent = stlContent.paragraph_format

    # Line spacing
    
    pfContent.line_spacing_rule =  WD_LINE_SPACING.DOUBLE
     
    ################## WRITING THE DOCUMENT ###############################################
    
    # Adding the Header to the document
    
    myRecords=setOfData
    myRecords1=setOfData1
    myRecords2=setOfData2

    ### scenario for security council ##########

    if (bodysession[0]=="S"):
        
        # Header

        p=header.add_paragraph("\t"+myTitle.upper(), style='New Heading')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p=header.add_paragraph("",style='subtitle')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("\n")
        p.add_run("Votes are as indicated in the provisional verbatim records of the Security Council,")
        p.add_run("\n")
        p.add_run('seventy-third year, 2018. The following symbols are used to indicate how each member voted:')
        p.add_run("\n")
        p.add_run('   Y	      Voted   Yes')
        p.add_run("\n")
        p.add_run('  N	     Voted   No')
        p.add_run("\n")
        p.add_run(' A	    Abstained')
        p.add_run("\n")
        p.add_run("\t"+'     NP    Not Participating')
        p.add_run("\n")
        p.add_run('Resolutions adopted without vote are indicated by a blank space')

        # Retrieving the number of records
        recordNumber = 0

        # Country list
        countries=[]     
        for datax in myRecords2[0]["votelist"]:
            countries.append(datax["memberstate"])

        for record in myRecords:
            recordNumber+=1
     

        # creation of the table
        table = document.add_table(rows=1,cols=16)
        print("tableau cree 0")
        table.style = 'TableGrid'

        first=True
        myRow = 0
        myCol = 0
        
        # Variable for managing the number of column to build
        columnToBuild=recordNumber
        
        for record1 in myRecords1:     
            
            # Check if we have already 15 records

            if myRow==15:
            
                myRow=0

                if myCol==16:

                    p=document.add_paragraph()

                    myBreak = p.add_run().add_break(WD_BREAK.PAGE)
                    
                    columnToBuild=(columnToBuild-15)
                    
                    if columnToBuild>=15 :
                    
                        table = document.add_table(rows=1,cols=16)

                        
                    if (columnToBuild<15):
                        
                        table = document.add_table(rows=1,cols=columnToBuild+1) 
                        
                        table.alignment = WD_TABLE_ALIGNMENT.LEFT


                    table.style = 'TableGrid'

                    myCol=0
 
            if myRow==0 and myCol==0:

                paragraph=table.cell(myRow,myCol).paragraphs[0]

                paragraph.text="S/RES/-"                
                
                paragraph_format = paragraph.paragraph_format
                paragraph_format.space_before = Inches(0.08)
                paragraph_format.space_after = Inches(0.08)    
                
                table.rows[0].cells[0].width = Inches(1.5)

                run = paragraph.runs

                font = run[0].font

                font.size= Pt(8)

                font.name = "Arial"

                # loop for the countries name to display in column

                for country in countries:

                    table.add_row()
                    
                    myRow=myRow+1
                    
                    paragraph=table.cell(myRow,myCol).paragraphs[0]
                    
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.space_before = Inches(0.08)
                    paragraph_format.space_after = Inches(0.08)

                    paragraph.text=country

                    run = paragraph.runs

                    font = run[0].font

                    font.size= Pt(8)

                    font.name = "Arial"

                    # size of the first column

                    table.cell(myRow,myCol).width=Inches(2.0)

                
                myRow=0
                myCol=myCol + 1

            if myRow==0 and myCol!=0:

                paragraph=table.cell(myRow,myCol).paragraphs[0]

                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER 
                
                #add_hyperlink(paragraph,record1["resnum"],"http://undocs.org/s/res/"+record1["docsymbol"])
                add_hyperlink(paragraph,record1["resnum"],"http://undocs.org/"+record1["docsymbol"])
               
                
                paragraph_format = paragraph.paragraph_format
                paragraph_format.space_before = Inches(0.08)
                paragraph_format.space_after = Inches(0.08)  
                
                table.rows[myRow].cells[myCol].width = Inches(0.53)   

                run = paragraph.runs

                font = run[0].font

                font.size= Pt(8)

                font.name = "Arial"


                for data in record1["votelist"]:
                    
                    myRow=myRow+1

                    paragraph=table.cell(myRow,myCol).paragraphs[0]

                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    paragraph.text=data["vote"]  
                    
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.space_before = Inches(0.08)
                    paragraph_format.space_after = Inches(0.08)   
                    
                    table.rows[myRow].cells[myCol].width = Inches(0.53)  

                    run = paragraph.runs

                    font = run[0].font

                    font.size= Pt(8)

                    font.name = "Arial"
                    

            myCol = myCol + 1

    add_page_number(document.sections[0].footer.paragraphs[0])
    return document


def generateWordDocITPREPS(paramTitle,paramSubTitle,bodysession,paramSection,paramNameFileOutput):
    
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
    setOfData=myCollection.find({'bodysession': bodysession,'section': paramSection})
    
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
    # new_sub_heading_style.base_style = styles['Heading 1']
    
    # Font settings
    pformat= new_sub_heading_style.paragraph_format
    pformat.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pformat.space_before = Pt(0)
    pformat.space_after = Pt(0)
    
    font = new_sub_heading_style.font
    font.name = 'Arial'
    font.size = Pt(7)
    font.italic = True
    font.color.rgb = RGBColor(0, 0, 0)

    ################## COMMITTEE ###############################################
    
    committee_style = styles.add_style('committee', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font settings
    pformat= committee_style.paragraph_format
    pformat.alignment=WD_ALIGN_PARAGRAPH.CENTER

    
    font = committee_style.font
    font.name = 'Arial'
    font.size = Pt(9)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)

    ################## SUBJECT ###############################################
    
    subject_style = styles.add_style('subject', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font settings
    pformat= subject_style.paragraph_format
    pformat.alignment=WD_ALIGN_PARAGRAPH.LEFT
    pformat.space_after=Inches(0.05)

    
    font = subject_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.color.rgb = RGBColor(0, 0, 0)

    ################## DOCSYMBOL ###############################################
    
    docsymbol_style = styles.add_style('docsymbol', WD_STYLE_TYPE.PARAGRAPH)
    
    # Font settings
    pformat= docsymbol_style.paragraph_format
    pformat.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    pformat.space_after=Inches(0.05)

    
    font = docsymbol_style.font
    font.name = 'Arial'
    font.size = Pt(8)
    font.color.rgb = RGBColor(0, 0, 0)

    ################## WRITING THE DOCUMENT ###############################################
    
    # Header Generation
    
    p=header.add_paragraph(myTitle.upper(), style='New Heading')
    #p=header.add_paragraph(myTitle, style='New Heading')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER    
    run=p.add_run("\n")

    # First line generation

    p=document.add_paragraph("The Committees discuss agenda items allocated to them by the Assembly.",style='New sub Heading')
    p=document.add_paragraph("The Committees report to the Assembly on the discussions held on each",style='New sub Heading')
    p=document.add_paragraph("item and forward recommendations for action in plenary",style='New sub Heading') 

    # Definition of the column names
    myRecords=setOfData

    # create some space with the header
    p.add_run("\n")
    p.add_run("\n")
    
    def getDocSymbols(myList):
        if len(myList)==1:
            add_hyperlink(row.cells[1].paragraphs[0],myList[0], Config.url_prefix+myList[0])

        else:
            myFinalResult=[]
            # storage for the root(s)
            myRoot=[]
            # storage for the Add(s)
            myAdd=[]
            # Storage for the Corr(s)
            myCorr=[]

            for myListElem in myList:
                recup=myListElem.split("/")

                # retrieving the root(s)
                if len(recup)==3 :
                    myRoot.append(myListElem)

                # retrieving the add(s)
                if len(recup)==4 and recup[3].startswith("Add"):
                    myAdd.append(myListElem)

                # retrieving the Corr(s)
                if len(recup)==4 and recup[3].startswith("Corr"):
                    myCorr.append(myListElem)

            myLink=""
            firstAdd=True
            firstCorr=True
            myLen=0 
            for root in myRoot:

                # generation of the root link
                # row.cells[1].paragraphs[0]=add_hyperlink(row.cells[1].paragraphs[0],root, Config.url_prefix+root)
                add_hyperlink(row.cells[1].paragraphs[0],root, Config.url_prefix+root)

                #adding of the Add if there is some values
                if len(myAdd)!=0:
                   
                   for add in myAdd:
                        if add.startswith(root):
                            if firstAdd==True:
                                # adding the '+' sign
                                myParagraph = row.cells[1].paragraphs[0]
                                myParagraph.add_run("+")
                                add_hyperlink(row.cells[1].paragraphs[0],"Add"+add[-1], Config.url_prefix+add)
                                # row.cells[1].paragraphs[0].text=" + "
                                # row.cells[1].paragraphs[0]=add_hyperlink(row.cells[1].paragraphs[0],"Add"+add[-1], Config.url_prefix+add)
                                firstAdd=False
                            else:
                                myParagraph = row.cells[1].paragraphs[0]
                                myParagraph.add_run("-")    
                                add_hyperlink(row.cells[1].paragraphs[0],add[-1], Config.url_prefix+add)

                # adding of the Corr if there is some values
                if len(myCorr)!=0:
                   for corr in myCorr:
                        if corr.startswith(root):                
                            # adding the '+' sign
                            myParagraph = row.cells[1].paragraphs[0]
                            myParagraph.add_run(", ")
                            add_hyperlink(row.cells[1].paragraphs[0],corr, Config.url_prefix+corr)

                # adding sign , when you have a new record
                myLen+=1
                if myLen<len(myRoot):
                    myParagraph = row.cells[1].paragraphs[0]
                    myParagraph.add_run(", ") 

    for record in myRecords:
        
        # creation of the table
        table = document.add_table(rows=1, cols=2)

        # paragraph=table.rows[0].cells[0].paragraphs[0]
        paragraph=table.rows[0].cells[0].merge(table.rows[0].cells[-1]).paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.text= record["committee"]
        paragraph.style = document.styles['committee']

        # writing the subjects
        for subject in record["subjects"]:

            # add a new row inside the table
            row = table.add_row()

            # add the content for the subject
            row.cells[0].paragraphs[0].text=subject['subject']
            row.cells[0].paragraphs[0].style = document.styles['subject']

            # add the content for the document symbol

            #add_hyperlink(row.cells[1].paragraphs[0],getDocSymbols(subject["docsymbols"]), Config.url_prefix+getDocSymbols(subject["docsymbols"]))
            #row.cells[1].paragraphs[0].text= getDocSymbols(subject["docsymbols"])
            getDocSymbols(subject["docsymbols"])
            row.cells[1].paragraphs[0].style = document.styles['docsymbol']


    widths = (Inches(22), Inches(2.00))
    for row in table.rows:
        # sizing the rows
        row.height = Cm(0.2)
        for idx, width in enumerate(widths):
            row.cells[idx].width = width

    sections = document.sections
    for section in sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)

    # Save the document
    add_page_number(document.sections[0].footer.paragraphs[0])
    return document