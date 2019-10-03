from app.forms import MissingFieldReportForm, MissingSubfieldReportForm

class Report(object):
    def __init__(self, name, title, description, form_class):
        self.name = name
        self.title = title
        self.description = description
        self.form_class = form_class

class ReportList(object):
    reports = [
        Report(
            name='missing_field',
            title='Missing Field Report',
            description='This report returns bib numbers and document symbols based on a particular body and session for the specified field. For the authority field you can insert the number or use the format body/session (eg:A/72) is alsp available for the search.',
            form_class= MissingFieldReportForm
        ),

        #Report(
        #    name='missing_subfield',
        #    title='Missing Subfield Report',
        #    description= 'This report returns bib numbers and document symbols based on a particular body and session for the specified field and subfield.',
        #    form_class= MissingSubfieldReportForm
        #)
    ]