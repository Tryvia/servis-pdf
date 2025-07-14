from datetime import datetime
from src.models.user import db
import uuid

class PdfFile(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(32), nullable=False)  # MD5 hash
    download_count = db.Column(db.Integer, default=0)
    last_download = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def increment_download_count(self):
        self.download_count += 1
        self.last_download = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'upload_time': self.upload_time.isoformat(),
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'download_count': self.download_count,
            'last_download': self.last_download.isoformat() if self.last_download else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<PdfFile {self.original_filename}>'


