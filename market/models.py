from market import db, login_manager
from market import bcrypt
from flask_login import UserMixin

def money_format(quantity):
    if quantity >= 1000:
        # separate with commas
        int_quantity_as_string = str(int(quantity))
        number_of_commas = (len(int_quantity_as_string)-1)//3

        for i in range(1, number_of_commas+1):
            # each three positions (starting from the end of the str)
            # plus the position comma added in the last iteration, add 
            # a comma
            int_quantity_as_string = f"{int_quantity_as_string[:-i*3-i+1]},{int_quantity_as_string[-i*3-i+1:]}"
        
        # add decimal point and float part
        if isinstance(quantity, float):
            quantity_as_string = str(quantity)
            decimal_point_index = quantity_as_string.find(".")
            quantity_as_string = f"{int_quantity_as_string}{quantity_as_string[decimal_point_index:]}"
        else:
            quantity_as_string = int_quantity_as_string

        return f"${quantity_as_string}"
    else:
        return f"${quantity}"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), unique=True, nullable=False)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=2000)
    items = db.relationship("Item", backref="owned_user", lazy=True)

    @property
    def prettier_budget(self):
        return money_format(self.budget)

    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode("utf-8")
    
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
    owner = db.Column(db.Integer(), db.ForeignKey("user.id"))
    def __repr__(self):
        return f"Item {self.name}"
    
    @property
    def cost_with_money_format(self):
        return money_format(self.price)

    def buy(self, user):
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()
    
    def sell(self, user):
        self.owner = None
        user.budget += self.price
        db.session.commit()

