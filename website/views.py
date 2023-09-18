from flask import Blueprint,render_template ,request ,flash, redirect, current_app,  make_response
from flask_login import  login_required, current_user
import PyPDF2
from .models import Note, User , Book 
from flask_uploads import UploadSet, configure_uploads, IMAGES, DOCUMENTS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import io 
# from werkzeug.utils import secure_filename
from . import db
import os

views = Blueprint('views',__name__)

cover_uploads = UploadSet('cover', IMAGES)
content_uploads = UploadSet('content', DOCUMENTS)

# Cấu hình tập tin tải lên cho ứng dụng Flask
configure_uploads(current_app, (cover_uploads, content_uploads))

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        if 'create_note' in request.form:
            note = request.form.get('note')
            book_id = request.form.get('book_id')  # Lấy giá trị book_id từ biểu mẫu
            if len(note) < 1:
                flash('Note is too short!', category='error')
            else:
                new_note = Note(data=note, user_id=current_user.id, book_id=book_id)  # Thêm book_id vào ghi chú
                db.session.add(new_note)
                db.session.commit()
        elif 'create_book' in request.form:
            book_title = request.form.get('book_title')
            author = request.form.get('author')
            cover = request.files.get('cover')
            content = request.files.get('content')

            if not book_title or not author:
                flash('Please fill in all the book details!', category='error')
            else:
                new_book = Book(title=book_title, author=author, cover=cover.filename, content=content.filename)
                db.session.add(new_book)
                db.session.commit()
                # Lưu tệp cover và content vào thư mục lưu trữ tùy chọn
                cover_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'cover')
                cover.save(os.path.join(cover_path, cover.filename))
                content_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'content')
                content.save(os.path.join(content_path, content.filename))
    notes = Note.query.all()
    books = Book.query.all()
    return render_template('home.html', user=current_user, notes=notes, books=books)


@views.route('/delete/<int:id>')
def delete(id):
    note_to_delete = Note.query.get_or_404(id)
    try:
        db.session.delete(note_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that note'
    
    
@views.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    note = Note.query.get_or_404(id)

    if request.method == 'POST':
        new_note_text = request.form.get('note')
        if len(new_note_text) < 1:
            flash('Note is too short!', category='error')
        else:
            note.data = new_note_text
            db.session.commit()
            flash('Note is updated!', category='success')
            return redirect('/')

    return render_template('update.html',  note=note)


@views.route('/view_content/<int:book_id>')
def view_content(book_id):
    book = Book.query.get_or_404(book_id)

    # Get the path to the content (PDF) file
    content_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'content')
    content_filename = book.content
    content_file_path = os.path.join(content_path, content_filename)

    # Check if the PDF file exists
    book = Book.query.get_or_404(book_id)
    pdf_file_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'content', book.content)

    try:
        # Open the PDF file in binary mode
        with open(pdf_file_path, 'rb') as pdf_file:
            # Read the binary data of the PDF file
            pdf_binary_data = pdf_file.read()
            
        # Set the appropriate response headers for PDF content
        response = make_response(pdf_binary_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={book_id}.pdf'
        
        return response

    except FileNotFoundError:
        # Handle the case where the PDF file is not found
        return "PDF file not found", 404


@views.route('/delete_book/<int:id>')
def delete_book(id):
    book_to_delete = Book.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that book'


@views.route('/update_book/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    book = Book.query.get_or_404(id)

    if request.method == 'POST':
        book_title = request.form.get('book_title')
        author = request.form.get('author')
        cover = request.files.get('cover')
        content = request.files.get('content')
        
        if not book_title or not author:
            flash('Please fill in both the book title and author!', category='error')
        else:
            # Kiểm tra và gán giá trị cho thuộc tính sách chỉ khi chúng tồn tại
            if book_title:
                book.title = book_title

           
            if author:
                book.author = author
            
            if content:
                book.content = content.filename
                content_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'content')
                content.save(os.path.join(content_path, content.filename))
                

            if cover:
                book.cover = cover.filename
                cover_path = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], 'cover')
                cover.save(os.path.join(cover_path, cover.filename))
               
            db.session.commit()
         
            flash('Book updated!', category='success')
            return redirect('/')

    return render_template('update_book.html', book=book)
