#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import datetime
import dateutil.parser
import babel
from flask import Flask, abort, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# artist_genre = db.Table('artist_genre',
#     db.Column('id',db.Integer, primary_key=True),
#     db.Column('artist_id', db.Integer, db.ForeignKey('artists.artist_id')),
#     db.Column('genre_id',db.Integer, db.ForeignKey('genre.genre_id'))
# )
#
#
# venue_genre = db.Table('venue_genre',
#     db.Column('id',db.Integer, primary_key=True),
#     db.Column('venue_id', db.Integer, db.ForeignKey('venues.venue_id')),
#     db.Column('genre_id',db.Integer, db.ForeignKey('genre.genre_id'))
# )
# class genre(db.Model):
#     __tablename__ = 'genre'
#     genre_id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, nullable=False)
#     description = db.Column(db.String, nullable=True)

Shows = db.Table('shows',
                 db.Column('show_id', db.Integer, primary_key=True),
                 db.Column('venue_id', db.Integer, db.ForeignKey('venues.venue_id')),
                 db.Column('artist_id', db.Integer,db.ForeignKey('artists.artist_id')),
                 db.Column('start_time', db.DateTime)
                 )


class Venue(db.Model):
    __tablename__ = 'venues'
    venue_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String))
    shows = db.relationship('Artist', secondary=Shows, cascade="all,delete", backref=db.backref('venues', lazy='joined'))
    website = db.Column(db.String(500), nullable=True)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(), nullable=True)


class Artist(db.Model):
    __tablename__ = 'artists'
    artist_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(), nullable=True)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = Venue.query.order_by(Venue.city)
    return render_template('pages/venues.html', areas=areas)
# TODO fix the display of citys


@app.route('/venues/search', methods=['POST'])
def search_venues():
    term=request.form.get('search_term', '')

    #results = Venue.query.filter(Venue.name.ilike('%term%')).all()
    results = Venue.query.filter(Venue.name.ilike('%'+term+'%'))

    return render_template('pages/search_venues.html', results=results, search_term=term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    #venue = Venue.filter(venue_id==venue_id)
    data = Venue.query.filter_by(venue_id=venue_id).first()
    past_shows= Artist.query.filter(Artist.venues.any(venue_id=venue_id)).all()
    upcoming_shows= Artist.query.filter(Artist.venues.any(venue_id=venue_id)).all()

    print(past_shows)

    print(upcoming_shows)
    data.past_shows=past_shows
    data.upcoming_shows=upcoming_shows


    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm(request.form)
    body={};
    genres=request.form.getlist('genres')
    try:
        venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, address=form.address.data,
                seeking_talent=False, genres=genres, seeking_description="", image_link="", facebook_link=form.facebook_link.data)
        db.session.add(venue)
        db.session.commit()
        body['name']=venue.name
        body['city']=venue.city
        body['address']= venue.address
        body['state']=venue.state
        body['genres']=venue.genres
        body['phone']=venue.phone
        body['venue_id']=venue.venue_id
        print(venue)
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + form.name.data+ ' could not be listed.')
    else:
        flash('Venue ' + form['name'].data +' was successfully listed!')

    return redirect(url_for('show_venue', venue_id=venue.venue_id))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(venue_id=venue_id).first()
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue could not be deleted.')
    else:
        flash('Venue  was successfully deleted!')

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [{
            "id": 4,
            "name": "Guns N Petals",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    form=ArtistForm()
    artist= Artist.query.filter(Artist.artist_id==artist_id).first()
    return render_template('pages/show_artist.html', form=form, artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(artist_id=artist_id).first()

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(venue_id=venue_id)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm(request.form)
    body={};
    genres=request.form.getlist('genres')
    try:
        artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data,
                        seeking_venue=False, genres=genres, seeking_description="", image_link="", facebook_link=form.facebook_link.data)
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + form.name.data+ ' could not be listed.')
        return redirect(url_for('index'))
    else:
        flash('Artist ' + form['name'].data +' was successfully listed!')
        return redirect(url_for('show_artist', artist_id=artist.artist_id))



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    venueShows = Venue.query.join(shows).join(Artist).filter(shows.c.venue_id==Venue.venue_id and shows.c.artist_id==Artist.artist_id).all()
    print(venueShows)

    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    return render_template('pages/shows.html', shows=venueShows)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    body={};
    genres=request.form.getlist('genres')
    try:
        show = Shows(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
        db.session.add(show)
        db.session.commit()

        body['artist_id']=show.artist_id
        body['venue_id']=show.venue_id
        body['start_time']=show.start_time

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show  could not be listed.')
    else:
        flash('Show was successfully listed!')

    return jsonify(body)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
