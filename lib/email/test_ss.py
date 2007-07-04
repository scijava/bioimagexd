import ssmtplib



conn = ssmtplib.SMTP_SSL('smtp.gmail.com',465)

# From here, you can use any method in smtplib

conn.login('kalle.pahajoki','XwE381My')

conn.ehlo()

conn.sendmail('kalle.pahajoki@gmail.com', 'kalle.pahajoki@gmail.com', "Testi")

conn.close()