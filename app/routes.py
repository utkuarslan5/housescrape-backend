from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import House
from app.forms import HouseForm

# Create a Blueprint for the routes related to houses
houses = Blueprint('houses', __name__)

@houses.route('/')
def index():
    # Retrieve all houses from the database
    all_houses = House.query.all()
    return render_template('index.html', houses=all_houses)

@houses.route('/add', methods=['GET', 'POST'])
def add_house():
    form = HouseForm()
    if form.validate_on_submit():
        # Create a new House instance from the form data
        new_house = House(
            title=form.title.data,
            location=form.location.data,
            price=form.price.data,
            description=form.description.data
        )
        # Add the new house to the database
        db.session.add(new_house)
        db.session.commit()
        flash('House added successfully!', 'success')
        return redirect(url_for('houses.index'))
    return render_template('add_house.html', form=form)

@houses.route('/edit/<int:house_id>', methods=['GET', 'POST'])
def edit_house(house_id):
    house = House.query.get_or_404(house_id)
    form = HouseForm(obj=house)
    if form.validate_on_submit():
        # Update the house with the form data
        house.title = form.title.data
        house.location = form.location.data
        house.price = form.price.data
        house.description = form.description.data
        db.session.commit()
        flash('House updated successfully!', 'success')
        return redirect(url_for('houses.index'))
    return render_template('edit_house.html', form=form, house=house)

@houses.route('/delete/<int:house_id>', methods=['POST'])
def delete_house(house_id):
    house = House.query.get_or_404(house_id)
    db.session.delete(house)
    db.session.commit()
    flash('House deleted successfully!', 'success')
    return redirect(url_for('houses.index'))