from flask import Blueprint, request, jsonify, send_file, url_for
import os
import uuid
import base64
from datetime import datetime, timedelta
import hashlib

pdf_storage_bp = Blueprint('pdf_storage', __name__)

# Diretório para armazenar os PDFs
PDF_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdf_storage')

# Garantir que o diretório existe
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

# Dicionário para armazenar metadados dos PDFs (em produção, usar banco de dados)
pdf_metadata = {}

@pdf_storage_bp.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Recebe um PDF em base64 e armazena no servidor
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'PDF data is required'}), 400
        
        pdf_base64 = data['data']
        filename = data.get('filename', 'relatorio_visita.pdf')
        
        # Remover prefixo data:application/pdf;base64, se existir
        if pdf_base64.startswith('data:application/pdf;base64,'):
            pdf_base64 = pdf_base64.split(',')[1]
        
        # Decodificar base64
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
        except Exception as e:
            return jsonify({'error': 'Invalid base64 data'}), 400
        
        # Gerar ID único para o arquivo
        file_id = str(uuid.uuid4())
        file_extension = '.pdf'
        stored_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(PDF_STORAGE_DIR, stored_filename)
        
        # Salvar arquivo
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Gerar hash para verificação de integridade
        file_hash = hashlib.md5(pdf_bytes).hexdigest()
        
        # Armazenar metadados
        pdf_metadata[file_id] = {
            'original_filename': filename,
            'stored_filename': stored_filename,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat(),
            'file_size': len(pdf_bytes),
            'file_hash': file_hash,
            'download_count': 0
        }
        
        # Gerar URL de download
        download_url = url_for('pdf_storage.download_pdf', file_id=file_id, _external=True)
        
        return jsonify({
            'success': True,
            'id': file_id,
            'file_id': file_id,
            'download_url': download_url,
            'filename': filename,
            'file_size': len(pdf_bytes)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_storage_bp.route('/download/<file_id>')
def download_pdf(file_id):
    """
    Permite download do PDF pelo ID
    """
    try:
        if file_id not in pdf_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        metadata = pdf_metadata[file_id]
        file_path = metadata['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Incrementar contador de downloads
        metadata['download_count'] += 1
        metadata['last_download'] = datetime.now().isoformat()
        
        # Retornar arquivo para download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=metadata['original_filename'],
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_storage_bp.route('/info/<file_id>')
def get_pdf_info(file_id):
    """
    Retorna informações sobre um PDF armazenado
    """
    try:
        if file_id not in pdf_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        metadata = pdf_metadata[file_id].copy()
        # Remover informações sensíveis
        metadata.pop('file_path', None)
        
        return jsonify({
            'success': True,
            'file_info': metadata
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_storage_bp.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """
    Remove arquivos antigos (mais de 7 dias)
    """
    try:
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)
        
        files_to_delete = []
        for file_id, metadata in pdf_metadata.items():
            upload_time = datetime.fromisoformat(metadata['upload_time'])
            if upload_time < cutoff_date:
                files_to_delete.append(file_id)
        
        for file_id in files_to_delete:
            metadata = pdf_metadata[file_id]
            file_path = metadata['file_path']
            
            # Remover arquivo do disco
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remover metadados
            del pdf_metadata[file_id]
            deleted_count += 1
        
        return jsonify({
            'success': True,
            'deleted_files': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_storage_bp.route('/list')
def list_pdfs():
    """
    Lista todos os PDFs armazenados (para debug/admin)
    """
    try:
        files_info = []
        for file_id, metadata in pdf_metadata.items():
            info = metadata.copy()
            info['file_id'] = file_id
            info.pop('file_path', None)  # Remover caminho por segurança
            files_info.append(info)
        
        return jsonify({
            'success': True,
            'files': files_info,
            'total_files': len(files_info)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

