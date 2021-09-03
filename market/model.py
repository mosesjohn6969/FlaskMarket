from flask import redirect, current_app, url_for, g, request
from market import db, login_manager, login, app
from market import bcrypt
from flask_login import UserMixin, current_user, login_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, Admin, expose
import os
import secrets


@app.before_request
def before_req():
    g.user = current_user


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def save_images(photo):
    hash_photo = secrets.token_urlsafe(10)
    file_extension = os.path.splitext(photo.filename)
    photo_name = hash_photo + file_extension
    file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
    photo.save(file_path)
    return photo_name


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if g.user.is_authenticated:
            return super(MyAdminIndexView, self).index()
        next_url = request.endpoint
        login_url = '%s?next=%s' % (url_for("login"), next_url)
        return redirect(login_url)

    def is_accessible(self):
        return current_user.is_authenticated


admin = Admin(app, name="Moses's store", template_mode='bootstrap4',
              index_view=MyAdminIndexView(name="DASHBOARD", menu_icon_type="fa", menu_icon_value="fa-home"))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    # full_name = db.Column(db.String(length=35), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=100000)
    items = db.relationship('Item', backref='owned_user', lazy=True)

    @property
    def prettier_budget(self):
        if len(str(self.budget)) >= 4:
            return f'₦{str(self.budget)[:-3]},{str(self.budget)[-3:]}'
        else:
            return f'₦{self.budget}'

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def can_purchase(self, item_obj):
        return self.budget >= item_obj.price

    def can_sell(self, item_obj):
        return item_obj in self.items


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    # category = db.Column(db.String(length=130), nullable=False, unique=True)
    # color = db.Column(db.String(length=130), nullable=False, unique=True)
    # quantity = db.Column(db.String(length=130), nullable=False, unique=True)
    # img_path = db.Column(db.String(length=130),  default="image.jpg", unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey("user.id"))

    def __repr__(self):
        return f'Item {self.name}'

    def buy(self, user):
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()

    def sell(self, user):
        self.owner = None
        user.budget += self.price
        db.session.commit()


admin.add_view(MyModelView(Person, db.session, name="PERSON", menu_icon_type="fa", menu_icon_value="fa-users"))
admin.add_view(MyModelView(User, db.session, name="USER", menu_icon_type="fa", menu_icon_value="fa-user-circle"))
admin.add_view(MyModelView(Item, db.session, name="PRODUCTS", menu_icon_type="fa", menu_icon_value="fa-shopping-cart"))
