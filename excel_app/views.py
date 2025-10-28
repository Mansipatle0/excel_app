import os
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from .models import ExcelUpload, Checklist
from .forms import UploadForm, ChecklistForm
import pandas as pd
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from typing import TYPE_CHECKING
import io

if TYPE_CHECKING:
    from django.db.models.manager import Manager
    from django.core.exceptions import ObjectDoesNotExist
    from django.http import HttpRequest, HttpResponse


def checklist_detail(request, excel_id):  # type: ignore
    record = get_object_or_404(ExcelUpload, id=excel_id)

    # Agar POST data se aaya ho (broadcast form se)
    note = request.GET.get('note', '')
    schedule = request.GET.get('schedule', '')
    selected_ids = request.GET.get('selected', '')

    context = {
        'record': record,
        'note': note,
        'schedule': schedule,
        'selected_ids': selected_ids,
        'generated_time': datetime.now(),
    }
    return render(request, 'excel_app/checklist_detail.html', context)


def download_sample_excel(request):  # type: ignore
    import pandas as pd
    from django.http import HttpResponse
    import tempfile
    import os
    
    # Create sample data
    data = {
        'Name': ['John Doe', 'Jane Smith'],
        'Phone': ['9876543210', '9876501234']
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
        
    # Write DataFrame to Excel
    df.to_excel(tmp_path, index=False, engine='openpyxl')
    
    # Read the file content
    with open(tmp_path, 'rb') as f:
        file_content = f.read()
    
    # Clean up temporary file
    os.unlink(tmp_path)
    
    # Prepare response
    response = HttpResponse(
        file_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=sample.xlsx'
    
    return response


def table_view(request):  # type: ignore
    records = ExcelUpload.objects.order_by('-date_added')  # type: ignore
    return render(request, 'excel_app/table.html', {'records': records})

def upload_view(request):  # type: ignore
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        # Check if this is an AJAX request (multiple ways to detect)
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or  # type: ignore
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        )
        
        if form.is_valid():
            f = request.FILES['file']
            source = form.cleaned_data.get('source','')
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(dest_dir, exist_ok=True)
            filepath = os.path.join(dest_dir, f.name)  # type: ignore
            with open(filepath, 'wb+') as dest:
                for chunk in f.chunks():  # type: ignore
                    dest.write(chunk)
            
            # Count rows (with timeout to prevent hanging)
            row_count = 0
            try:
                if f.name.lower().endswith(('.xls','.xlsx')):  # type: ignore
                    # For large Excel files, just count rows without loading all data
                    import pandas as pd
                    # Read only first 1000 rows for performance, or use a more efficient method
                    df = pd.read_excel(filepath, engine='openpyxl', nrows=1000)
                    row_count = len(df)
                    # If we hit the limit, indicate that there are more rows
                    if row_count == 1000:
                        row_count = "1000+"  # Indicate there are more rows
                else:
                    # For CSV files, we can count lines more efficiently
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as csv_file:
                        row_count = sum(1 for line in csv_file) - 1  # Subtract 1 for header
            except Exception as e:
                # If counting fails, set to 0 but don't fail the upload
                row_count = "unknown"
                print(f"Row counting failed: {e}")
            
            rec = ExcelUpload.objects.create(  # type: ignore
                excel_file = os.path.join('uploads', f.name),  # type: ignore
                excel_name = f.name,  # type: ignore
                source = source,
                count = 0 if row_count == "unknown" else row_count
            )
            
            # Always return JSON for AJAX requests, regardless of how they're detected
            if is_ajax:
                message = f'Uploaded {f.name}'  # type: ignore
                if row_count != "unknown":
                    message += f' ({row_count} rows)'
                else:
                    message += ' (row count unavailable)'
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            else:
                message = f'Uploaded {f.name}'  # type: ignore
                if row_count != "unknown":
                    message += f' ({row_count} rows)'
                else:
                    message += ' (row count unavailable)'
                messages.success(request, message)
                return redirect('excel_app:table_view')
        else:
            # Always return JSON for AJAX requests, regardless of how they're detected
            if is_ajax:
                # Get form errors
                errors = []
                if form.errors:
                    for field, error_list in form.errors.items():
                        errors.append(f"{field}: {', '.join(error_list)}")
                if not errors:
                    errors.append("Form validation failed. Please check your inputs.")
                return JsonResponse({
                    'success': False,
                    'message': ' '.join(errors)
                })
            else:
                messages.error(request, 'Form validation failed. Please check your inputs.')
                return render(request, 'excel_app/upload.html', {'form': form})
    else:
        form = UploadForm()
    return render(request, 'excel_app/upload.html', {'form': form})

def delete_record(request, pk):  # type: ignore
    try:
        record = ExcelUpload.objects.get(pk=pk)  # type: ignore
    except ExcelUpload.DoesNotExist:  # type: ignore
        messages.error(request, "Record not found or already deleted.")
        return redirect('excel_app:table_view')

    # File delete safely
    file_path = os.path.join(settings.MEDIA_ROOT, str(record.excel_file))
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"File delete error: {e}")

    record.delete()
    messages.success(request, f"'{record.excel_name}' deleted successfully.")
    return redirect('excel_app:table_view')

def checklist_view(request, excel_id=None):  # type: ignore
    excel_files = ExcelUpload.objects.all().order_by('-date_added')  # type: ignore
    selected_excel = None  # type: ignore
    contacts = None
    note = ''
    schedule = ''

    # ✅ Agar excel_id URL se mila, to direct load kar do
    if excel_id:
        try:
            selected_excel = ExcelUpload.objects.get(id=excel_id)  # type: ignore
            df = pd.read_excel(selected_excel.excel_file.path)  # type: ignore
            contacts = df.to_dict(orient='records')
            messages.success(request, f"Loaded {len(contacts)} contacts from {selected_excel.excel_name}")
        except Exception as e:
            messages.error(request, f"Error loading Excel: {e}")

    # ✅ Agar POST se aaya to pehle jaisa hi rakho
    elif request.method == 'POST':
        excel_id = request.POST.get('excel_select')
        note = request.POST.get('note', '')
        schedule = request.POST.get('schedule', '')

        if excel_id:
            try:
                selected_excel = ExcelUpload.objects.get(id=excel_id)  # type: ignore
                df = pd.read_excel(selected_excel.excel_file.path)  # type: ignore
                contacts = df.to_dict(orient='records')

                if schedule:
                    Checklist.objects.create(  # type: ignore
                        excel=selected_excel,
                        note=note,
                        scheduled_at=schedule,
                        status='pending'
                    )
                    messages.success(request, f"Schedule saved and loaded {len(contacts)} contacts.")
            except Exception as e:
                messages.error(request, f"Error reading Excel: {e}")

    recent_checklists = Checklist.objects.all().order_by('-created_at')  # type: ignore

    return render(request, 'excel_app/checklist.html', {
        'excel_files': excel_files,
        'selected_excel': selected_excel,
        'contacts': contacts,
        'note': note,
        'schedule': schedule,
        'recent_checklists': recent_checklists,
    })

def view_excel_data(request, pk):  # type: ignore
    record = get_object_or_404(ExcelUpload, pk=pk)
    file_path = os.path.join(settings.MEDIA_ROOT, str(record.excel_file))

    try:
        if file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_csv(file_path)
        data_html = df.head(50).to_html(classes='table table-bordered table-striped', index=False)
    except Exception as e:
        data_html = f"<p>Error reading file: {e}</p>"

    return render(request, 'excel_app/view_excel.html', {
        'record': record,
        'data_html': data_html
    })


def bulk_delete(request):  # type: ignore
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_records')
        if selected_ids:
            ExcelUpload.objects.filter(id__in=selected_ids).delete()  # type: ignore
            messages.success(request, f"{len(selected_ids)} record(s) deleted successfully!")
        else:
            messages.warning(request, "No records selected.")
    return redirect('excel_app:table_view')


def broadcast_api(request):  # type: ignore
    if request.method == "POST":
        import json
        import requests
        data = json.loads(request.body)

        note = data.get("note", "")
        schedule = data.get("schedule", "")
        selected_ids = data.get("selected_ids", [])
        excel_id = data.get("excel_id")

        try:
            # Get selected Excel
            excel = ExcelUpload.objects.get(id=excel_id)  # type: ignore

            # Save checklist entry
            checklist = Checklist.objects.create(  # type: ignore
                excel=excel,
                note=note,
                scheduled_at=schedule,
                status="pending"
            )

            # Read the Excel file to get phone numbers
            df = pd.read_excel(excel.excel_file.path)  # type: ignore
            
            # Extract phone numbers from the 'Phone' column
            phone_numbers = []
            if 'Phone' in df.columns:
                phone_numbers = df['Phone'].dropna().tolist()
            else:
                # If no 'Phone' column, try to find any column that might contain phone numbers
                for col in df.columns:
                    if 'phone' in col.lower() or 'mobile' in col.lower() or 'tel' in col.lower():
                        phone_numbers = df[col].dropna().tolist()
                        break
            
            # If still no phone numbers found, return an error
            if not phone_numbers:
                return JsonResponse({
                    "success": False, 
                    "message": "No phone numbers found in the Excel file. Please ensure there is a 'Phone' column with valid phone numbers."
                })

            # Call WhatsApp API for each phone number
            whatsapp_url = "https://graph.facebook.com/v22.0/223427244188062/messages"
            whatsapp_headers = {
                "Authorization": "Bearer EAAMO9wPuFi0BPxLeZBxRi5ZCBtLrIZBpqJP5BpvNbgE1gxZADWgMEw3SbPWUzQyQHAhwjjIwBLufQC16pGf1o4KYgWOH0Hm10qUkFLTxfXVSiqHCn4DQFfLEZCE9VribnFhkZBAvuN2oWap59uhURana4TK5n4fMZC36HlBD28AUpvQDmi87a9ZBcs0FenymxW10tpjwy7RcP8mYKZBxnlDAExg89mRwn8f5AcEmKNFYTLe21qoKsU2PCotFmtQhzDAwZD",
                "Content-Type": "application/json"
            }
            
            successful_sends = 0
            failed_sends = 0
            errors = []
            
            # Send message to each phone number
            for phone in phone_numbers:
                # Clean the phone number (remove spaces, dashes, etc.)
                clean_phone = str(phone).replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                
                # Add country code if missing (assuming India with +91)
                if not clean_phone.startswith('+') and not clean_phone.startswith('91'):
                    clean_phone = '91' + clean_phone
                
                # If it starts with +91, remove the + and keep 91
                if clean_phone.startswith('+91'):
                    clean_phone = '91' + clean_phone[3:]
                
                whatsapp_data = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": "hello_world",
                        "language": {
                            "code": "en_US"
                        }
                    }
                }

                # Make the API call
                response = requests.post(whatsapp_url, headers=whatsapp_headers, json=whatsapp_data)
                
                # Print detailed response information for debugging
                print(f"WhatsApp API Request to {clean_phone}: {whatsapp_url}")
                print(f"WhatsApp API Response Status: {response.status_code}")
                try:
                    response_json = response.json()
                    print(f"WhatsApp API Response JSON: {response_json}")
                except:
                    print(f"WhatsApp API Response Text: {response.text}")
                
                # Check if the message was sent successfully
                if response.status_code == 200:
                    successful_sends += 1
                else:
                    failed_sends += 1
                    errors.append(f"Failed to send to {clean_phone}: {response.status_code}")
            
            # Update checklist status based on results
            if successful_sends > 0:
                checklist.status = "approved"
                checklist.save()
                
                if failed_sends == 0:
                    return JsonResponse({
                        "success": True, 
                        "message": f"Broadcast saved and WhatsApp messages sent successfully to {successful_sends} recipients!"
                    })
                else:
                    return JsonResponse({
                        "success": True, 
                        "message": f"Broadcast saved. WhatsApp messages sent to {successful_sends} recipients, failed to send to {failed_sends} recipients.",
                        "errors": errors
                    })
            else:
                return JsonResponse({
                    "success": False, 
                    "message": f"Broadcast saved but failed to send WhatsApp messages to all {failed_sends} recipients.",
                    "errors": errors
                })

        except ExcelUpload.DoesNotExist:  # type: ignore
            return JsonResponse({"success": False, "error": "Excel file not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

