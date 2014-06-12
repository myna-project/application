#-------------------------------------------------------------------------------
# Copyright (c) 2014 Proxima Centauri srl <info@proxima-centauri.it>.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Public License v3.0
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/gpl.html
# 
# Contributors:
#     Proxima Centauri srl <info@proxima-centauri.it> - initial API and implementation
#-------------------------------------------------------------------------------
import logging 
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

logger = logging.getLogger(__name__)

def send_mail(subject, text, to, mail_config, general_config):
    msg = MIMEText(text)
    
    from_address = _build_from_address(mail_config, general_config)
    
    logger.debug("Send mail from %s to %s", from_address, to)
    
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to
    msg['Date'] = formatdate(localtime=True)
     
    try:
        s = smtplib.SMTP(mail_config.smtp)
        s.sendmail(from_address, to.split(","), msg.as_string()) 
        s.quit()
    except Exception, e:
        logger.info('Unable to send alarm mail %s', e)
        
def _build_from_address(mail_config, general_config):
    if mail_config.from_address != None and  mail_config.from_address != '':
        return mail_config.from_address
    
    if general_config.plantid != None and general_config.plantid != '':
        return  general_config.plantid + "@myna-project.org"
    
    return "myna_raspberry@myna-project.org"
