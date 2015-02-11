import re
import webapp2
import jinja2
from pyPdf import PdfFileWriter, PdfFileReader
import os
import StringIO
import reportlab

from google.appengine.ext import db

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from time import strftime
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfbase.ttfonts import TTFont

#python /home/cameron/Desktop/GAE/google_appengine/dev_appserver.py /home/cameron/Projects/'Google App Engine'/helloworld/


pdfmetrics.registerFont(TTFont('Tangerine_Bold', 'Tangerine_Bold.ttf'))
pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

# name = 'Cameron Sima'
date = strftime("%m-%d-%Y")

dates = {
	'01': 'first', '02': 'second',
	'03': 'third', '04': 'fourth',
	'05': 'fifth', '06': 'sixth', '07': 'seventh',
	'08': 'eighth', '09': 'ninth',
	'10': 'tenth', '11': 'eleventh',
	'12': 'twelfth', '13': 'thirteenth',
	'14': 'fourteenth', '15': 'fifteenth',
	'16': 'sixteenth', '17': 'seventeenth',
	'18': 'eighteenth', '19': 'ninteenth',
	'20': 'twentieth', '21': 'twenty-first',
	'22': 'twenty-second', '23': 'twenty-third',
	'24': 'twenty-fourth', '25': 'twenty-fifth',
	'26': 'twenty-seventh', '28': 'twenty-eighth',
	'29': 'twenty-ninth', '30': 'thirtieth',
	'31': 'thirty-first'
}

months = {
	'01': 'January', '02': 'February',
	'03': 'March', '04': 'April',
	'05': 'May', '06': 'June',
	'07': 'July', '08': 'August',
	'09': 'September', '10': 'October',
	'11': 'November', '12': 'December'
	
}

class DB(db.Model):
	name = db.StringProperty(required=True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class InputHandler(Handler):
	def get(self):
		self.render('cert_form.html')

	def post(self):
		name = self.request.get('name')
		title = self.request.get('title')
		address = self.request.get('address')
		address2 = self.request.get('address2')
		city = self.request.get('city')
		state = self.request.get('state')
		zipcode = self.request.get('zipcode')
		email = self.request.get('email')
		phone = self.request.get('phone')
		site = self.request.get('site')
		training = self.request.get('training')
		agree = self.request.get('accept')

		if name and address and city and state and zipcode and email:
			a = DB(name=name)
			a.put()
			self.redirect('/payment')
			self.redirect('/payment/%s' % a.key().id())
		else:
			error = "Please fill all required fields."
			self.render('cert_form.html', error=error)

class PaymentHandler(Handler):
	def get(self, id):
			# a = db.Key.from_path('DB', int(id))
			# post = db.get(a)
			# cert_name = post.name
			# self.render('payment.html')
			#self.response.write(str(id))
			ppid = str(id)
			self.render("payment.html", ppid=ppid)

# class Listener(Handler):
# 	def get(self):
# 		self.response

class PDFHandler(Handler):
	def get(self):
		# a = db.Key.from_path('DB', int(id))
		# post = db.get(a)
		# cert_name = post.name
		self.render('pdf.html')

	def post(self):
		name = self.request.get('name')

		if name:
		# if not id:
		# 	self.error(500)
		# 	return
			try:

				q = db.Query(DB)
				q = DB.all()
				q.filter('name =', name)
				e = q.get()
				cert_name = e.name
				d = [dates[x] for x in dates if x == date.split('-')[1]]
				m = [months[x] for x in months if x == date.split('-')[0]]
				self.response.write(str(m) + str(d))
				date_str = "     In witness whereof we have placed our name on this,"
				date_str2 = "the {0} day of {1}, in the year two thousand fifteen." \
				.format(str(d).split("'")[1], str(m).split("'")[1])

				packet = StringIO.StringIO()
				# create a new PDF with Reportlab
				can = canvas.Canvas(packet, pagesize=letter)
				text = can.beginText()
				text2 = can.beginText()
				text.setTextOrigin(10.3*cm, 10.8*cm)
				text2.setTextOrigin(8.8*cm, 7.7*cm)
				text2.setFont("Tangerine_Bold", 20)
				text.setFont('VeraBd', 20)
				text.textLine(cert_name.upper())
				text2.textLine(date_str)
				text2.textLine(date_str2)
				can.drawText(text)
				can.drawText(text2)

				# can.drawString(300, 310, name)
				can.save()

				#move to the beginning of the StringIO buffer
				packet.seek(0)
				new_pdf = PdfFileReader(packet)
				# read your existing PDF
				existing_pdf = PdfFileReader(file("Certificate.pdf", "rb"))
				output = PdfFileWriter()
				# add the "watermark" (which is the new pdf) on the existing page
				page = existing_pdf.getPage(0)
				page.mergePage(new_pdf.getPage(0))
				output.addPage(page)
				outputstream = StringIO.StringIO()
				output.write(outputstream)
				self.response.headers['Content-Type'] = 'application/pdf'
				self.response.headers['Content-Disposition'] = 'attachment; filename=Certificate.pdf'
				self.response.headers['Content-Transfer-Encoding'] = 'binary'
				self.response.out.write(outputstream.getvalue())

			except:
				error = "There was an error.\n Please either re-enter your name \
				exactly as you typed it in field one of the application form, or check \
				your email to ensure payment has been successful."
				self.render('pdf.html', error=error)
			else:
				error = "Please enter you full name, as it appears on your certificate."
				self.render('pdf.html', error=error)


application = webapp2.WSGIApplication([
	(r'/', InputHandler),
	(r'/payment/([0-9]+)', PaymentHandler),
	#('/([0-9]+)', PDFHandler),
	(r'/payment_received/', PDFHandler),
    #(r'/key=(.)+', PDFHandler),
    (r'/payment_successful_pdf_rdy/', PDFHandler),
    #(r'/listener', Listener),
], debug=True)
