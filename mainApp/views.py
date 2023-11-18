from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
import string
import random
import imaplib
import email
from datetime import datetime
from pytz import utc

#IMAP Credentials
USERNAME = "catch_all_inbox@example.com"
PASSWORD = "inbox_password"
SERVER = "mail.example.com"
PORT = 993

domains = ['inboxx.xyz']

# Create your views here.
def home(request):
    request.session.set_test_cookie()

    # Getting active inboxes
    totalEmailIds = request.session.get('totalEmailIds')
    if totalEmailIds == None:
        # Creating a random inbox if no active inboxes
        randomUsername = ''.join(random.choices(string.ascii_lowercase, k=7))
        request.session['totalEmailIds'] = 1
        totalEmailIds = 1
        emailId = randomUsername + "@" + domains[0]
        request.session['email0'] = emailId

    context = {'emails': [request.session[f'email{i}'] for i in range(totalEmailIds)]}
    return render(request, 'index.html', context)

def updateEmails(emailID):
    # Connect to the IMAP server
    imap_server = imaplib.IMAP4_SSL(SERVER, PORT)
        
    # Login to the Outlook account
    imap_server.login(USERNAME, PASSWORD)
    
    # Select the mailbox to fetch emails from (e.g., 'INBOX')
    mailbox = 'INBOX'
    imap_server.select(mailbox)
    
    # Search for all emails in the selected mailbox
    result, data = imap_server.search(None, f"TO {emailID}")
    
    emails = {}
    row = 0
    if result == 'OK':
        email_ids = data[0].split()
    
        for email_id in email_ids:
            # Fetch the email data for the given email ID
            result, email_data = imap_server.fetch(email_id, '(RFC822)')
    
            if result == 'OK':
                # Parse the email data
                raw_email = email_data[0][1]
                email_message = email.message_from_bytes(raw_email)
    
                # Get the HTML content of the email
                html_content = None
                for part in email_message.walk():
                    if part.get_content_type() == 'text/html':
                        html_content = part.get_payload(decode=True).decode()
                        
                sender = email_message['From'].split('<')[0]
                sender_email = email_message['From'].split('<')[1][:-1]
                receiver = email_message['To']
                subject = email_message['subject']
                DateTime = email_message['date']
                
                if 'UTC' in DateTime:
                    DateTime = DateTime[:-6]
                DateTime = datetime.strptime(DateTime, '%a, %d %b %Y %H:%M:%S %z').astimezone(utc)
                
                date = DateTime.strftime("%d-%m-%Y")
                time = DateTime.time()
                
                emails[row] = {'sender': sender, 'sender_email': sender_email, 'subject': subject, 'content': html_content, 'date': date, 'time': time}
                row += 1
    
    # Logout and close the connection
    imap_server.logout()
    return emails
    
@never_cache
def get_emails(request):
    
    # Check for authority of inbox
    emailID = request.GET['id']
    
    totalEmailIds = request.session.get('totalEmailIds')
    if totalEmailIds == None:
        totalEmailIds = 0
    activeInboxes = [request.session[f'email{i}'] for i in range(totalEmailIds)]
    if emailID not in activeInboxes:
        return JsonResponse({'responseCode': 400, 'message': 'Unauthorized Inbox Requested'})
    
    # Update all emails
    emails = updateEmails(emailID)
    if emails == False:
        context = {'responseCode': 400, 'message': 'Connection failure'}
    else:
        context = {'responseCode': 200, 'emails': emails}
    return JsonResponse(context)
    

@never_cache
def create_inbox(request):
    userID = request.GET['username']
    domainID = request.GET['domain']
    emailId = userID + '@' + domainID
    
    if domainID not in domains:
        return JsonResponse({'responseCode': 400, 'message': 'Unauthorized domain requested.'})
    elif len(userID)<1:
        return JsonResponse({'responseCode': 400, 'message': 'Username must be of non-zero length.'})
    elif userID.isalnum() == False:
        return JsonResponse({'responseCode': 400, 'message': 'Username must be alpha-numeric only.'})
    
    totalEmailIds = request.session.get('totalEmailIds')
    if totalEmailIds==None:
        totalEmailIds = 0
    
    if totalEmailIds >=3:
        return JsonResponse({'responseCode': 400, 'message': 'Maximum inbox limit reached'})
    elif emailId in [request.session[f'email{i}'] for i in range(totalEmailIds)]:
        return JsonResponse({'responseCode': 400, 'message': 'Email already assigned to the user'})
    else:
        request.session[f'email{totalEmailIds}'] = emailId
        request.session['totalEmailIds'] += 1
        return JsonResponse({'responseCode': 200})

@never_cache
def delete_inbox(request):
    emailId = request.GET['emailId']
    totalEmailIds = request.session.get('totalEmailIds')
    
    if totalEmailIds == None:
        totalEmailIds = 0
        
    emails = [request.session[f'email{i}'] for i in range(totalEmailIds)]
    
    if emailId not in emails:
        return JsonResponse({'responseCode': 400, 'message': 'Inbox not found'})
    else:
        emails.remove(emailId)
        for i in range(len(emails)):
             request.session[f'email{i}'] = emails[i]
        del request.session[f'email{len(emails)}']
        request.session['totalEmailIds'] = len(emails)
        return JsonResponse({'responseCode': 200})
        
        
@never_cache
def delete_email(request):
    
    deleteStatus = False
    
    senderEmail = request.GET['sender']
    emailDate = request.GET['date']
    emailId = request.GET['email']
    
    totalEmailIds = request.session.get('totalEmailIds')
    
    if totalEmailIds == None:
        totalEmailIds = 0
        
    emails = [request.session[f'email{i}'] for i in range(totalEmailIds)]
    
    if emailId not in emails:
        return JsonResponse({'responseCode': 400, 'message': 'Unauthorized request'})
    else:
        
        # Connect to the IMAP server
        imap_server = imaplib.IMAP4_SSL(SERVER, PORT)
            
        # Login to the Outlook account
        imap_server.login(USERNAME, PASSWORD)
        
        # Select the mailbox to fetch emails from (e.g., 'INBOX')
        mailbox = 'INBOX'
        imap_server.select(mailbox)
        
        # Search for all emails in the selected mailbox
        result, data = imap_server.search(None, f"TO {emailId}")
        
        emails = {}
        row = 0
        if result == 'OK':
            email_ids = data[0].split()
        
            for email_id in email_ids:
                # Fetch the email data for the given email ID
                result, email_data = imap_server.fetch(email_id, '(RFC822)')
        
                if result == 'OK':
                    # Parse the email data
                    raw_email = email_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    DateTime = email_message['date']
                
                    if 'UTC' in DateTime:
                        DateTime = DateTime[:-6]
                    DateTime = datetime.strptime(DateTime, '%a, %d %b %Y %H:%M:%S %z').astimezone(utc)
                    
                    if (senderEmail == email_message['From'].split('<')[1][:-1]) and (emailDate == str(DateTime.strftime("%d-%m-%Y")) + " " + str(DateTime.time())):
                        imap_server.store(email_id, '+FLAGS', '\\Deleted')
                        deleteStatus = True
                        break
        
        # Permanently remove the deleted emails
        imap_server.expunge()
        
        # Logout and close the connection
        imap_server.logout()
        
        if deleteStatus:
            return JsonResponse({'responseCode': 200})
        else:
            return JsonResponse({'responseCode': 400, 'message': 'Email not found'})
