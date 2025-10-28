from django.db import models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import Manager

class ExcelUpload(models.Model):
    excel_file = models.FileField(upload_to='uploads/')
    excel_name = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True)
    count = models.PositiveIntegerField(default=0)  # type: ignore
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.excel_name)

    objects: "Manager[ExcelUpload]"  # type: ignore

class Checklist(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('approved','Approved'),
        ('rejected','Rejected'),
    ]
    excel = models.ForeignKey(ExcelUpload, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    scheduled_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(f"{self.status} - {self.scheduled_at}")

    objects: "Manager[Checklist]"  # type: ignore