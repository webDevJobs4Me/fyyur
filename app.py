#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from datetime import datetime
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


# Shows = db.Table('shows',
#      db.Column('show_id', db.Integer, primary_key=True),
#      db.Column('venue_id', db.Integer, db.ForeignKey('venues.venue_id')),
#      db.Column('artist_id', db.Integer,db.ForeignKey('artists.artist_id')),
#      db.Column('start_time', db.DateTime)
#      )

class Shows(db.Model):
    __tablename__ = 'shows'
    show_id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.artist_id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.venue_id'))
    start_time = db.Column(db.DateTime)
    artist = db.relationship("Artist", back_populates="venues")
    venue = db.relationship("Venue", back_populates="artists")

class Venue(db.Model):
    __tablename__ = 'venues'
    venue_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String))
    artists = db.relationship("Shows", cascade="all,delete", backref=db.backref("venues_from_artists", lazy="joined"))
    website = db.Column(db.String(500), nullable=True)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(), nullable=True)
    @classmethod
    # def complete(self):
    #     doc = "The complete selfproperty."
    #     past_shows = Venue.query.filter(Venue.artists.any(artist_id=1)).all().filter(shows.start_time < datetime.today()).all()
    #     upcoming_shows = Venue.query.join(Artist).filter(venue_id=self.venue_id).all().filter(shows.start_time > datetime.today()).all()
    #     return {
    #     'venue_id': self.venue_id,
    #     'name': self.name,
    #     'genres': self.genres,
    #     'state' : self.state,
    #     'city' : self.city,
    #     'address' : self.address,
    #     'image_link': self.image_link,
    #     'facebook_link' : self.facebook_link,
    #     'phone' : self.phone,
    #     'website': self.website,
    #     'seeking_talent':self.seeking_talent,
    #     'seeking_description' :self.seeking_description,
    #
    #     'past_shows': [{
    #         'artist_id': show.artist.artist_id,
    #         'artist_name': show.artist.name,
    #         'artist_image_link': show.artist.image_link,
    #         'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    #     } for show in past_shows],
    #     'upcoming_shows': [{
    #         # 'artist_id': show.artist.artist_id,
    #         # 'artist_name': show.artist.name,
    #         # 'artist_image_link': show.artist.image_link,
    #         #'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    #     } for show in upcoming_shows],
    #     'past_shows_count': len(past_shows),
    #     'upcoming_shows_count': len(upcoming_shows)
    #     }
    def __repr__(self):
        return self.name

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
    venues = db.relationship("Shows", cascade="all,delete", backref=db.backref('artists_from_venues', lazy='joined'))
    def __repr__(self):
        return self.name
    @classmethod
    def complete(self):
        doc = "The complete self property."
        past_shows = db.session.query(Artist, Venue, Shows).join(Shows, Shows.artist_id ==self.artist_id).join(Venue,Venue.venue_id==Shows.venue_id).filter(Shows.start_time < datetime.today())
        upcoming_shows = db.session.query(Artist, Venue, Shows).join(Shows, Shows.artist_id ==self.artist_id).join(Venue,Venue.venue_id==Shows.venue_id).filter(Shows.start_time > datetime.today())
        return {
        'artist_id': self.artist_id,
        'name': self.name,
        'genres': self.genres,
        'state' : self.state,
        'city' : self.city,
        'image_link': self.image_link,
        'facebook_link' : self.facebook_link,
        'phone' : self.phone,
        'seeking_venue':self.seeking_venue,
        'seeking_description' :self.seeking_description,

        'past_shows': [{
            'artist_id': show.Artist.artist_id,
            'artist_name': show.Artist.name,
            'artist_image_link': show.Artist.image_link,
            'start_time': show.Shows.start_time.strftime("%m/%d/%Y, %H:%M")
        } for show in past_shows],
        'upcoming_shows': [{
            'artist_id': show.Artist.artist_id,
            'artist_name': show.Artist.name,
            'artist_image_link': show.Artist.image_link,
            'start_time': show.Shows.start_time.strftime("%m/%d/%Y, %H:%M")
        } for show in upcoming_shows],
        # 'past_shows_count': len(past_shows),
        # 'upcoming_shows_count': len(upcoming_shows)
        }


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
    areas = Venue.query.order_by(Venue.city).all()

    return render_template('pages/venues.html', areas=areas)
# TODO fix the display of citys


@app.route('/venues/search', methods=['POST'])
def search_venues():
    term=request.form.get('search_term', '')
    results = Venue.query.filter(Venue.name.ilike('%'+term+'%'))
    return render_template('pages/search_venues.html', results=results, search_term=term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    #venue = Venue.filter(venue_id==venue_id)
    data = Venue.query.filter(Venue.venue_id==venue_id).first()
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
    term=request.form.get('search_term', '')
    results = Artist.query.filter(Artist.name.ilike('%'+term+'%'))
    return render_template('pages/search_artists.html', results=results, search_term=term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    form=ArtistForm()
    artist= Artist.query.filter(Artist.artist_id==artist_id).first().complete()
    return render_template('pages/show_artist.html', form=form, artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(artist_id=artist_id).first()
    form.name.data=artist.name
    form.genres.data=artist.genres
    form.city.data=artist.city
    form.state.data=artist.state
    form.phone.data=artist.phone
    form.facebook_link.data=artist.facebook_link
    form.image_link.data=artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    form = ArtistForm(request.form)
    body={};
    genres=request.form.getlist('genres')

    try:
        artist= Artist.query.filter_by(artist_id=artist_id).first()
        artist.name=form.name.data
        artist.city=form.city.data
        artist.state=form.state.data
        artist.phone=form.phone.data
        artist.genres=genres
        artist.image_link=form.image_link.data
        artist.facebook_link=form.facebook_link.data
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
        flash('Artist ' + form['name'].data +' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(venue_id=venue_id).first()
    form.name.data=venue.name
    form.address.data=venue.address
    form.genres.data=venue.genres
    form.city.data=venue.city
    form.state.data=venue.state
    form.phone.data=venue.phone
    form.facebook_link.data=venue.facebook_link
    form.image_link.data=venue.image_link
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    form = VenueForm(request.form)
    body={};
    genres=request.form.getlist('genres')

    try:
        venue = Venue.query.filter_by(venue_id=venue_id).first()
        venue.name=form.name.data
        venue.city=form.city.data
        venue.state=form.state.data
        venue.phone=form.phone.data
        venue.genres=genres
        venue.address=form.address.data
        venue.facebook_link=form.facebook_link.data
        venue.website=form.website.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + form.name.data+ ' could not be updated.')
        return redirect(url_for('index'))
    else:
        flash('Venue ' + form['name'].data +' was successfully updated!')
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

@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.filter_by(artist_id=artist_id).first()
        db.session.delete(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist could not be deleted.')
    else:
        flash('Artist was successfully deleted!')

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    artistShows= db.session.query(Artist, Venue, Shows).join(Shows, Shows.artist_id ==Artist.artist_id).join(Venue,Venue.venue_id==Shows.venue_id)
    return render_template('pages/shows.html', shows=artistShows)

@app.route('/shows/search', methods=['POST'])
def search_shows():
    term=request.form.get('search_term', '')
    results = db.session.query(Artist, Venue, Shows).join(Shows, Shows.artist_id ==Artist.artist_id).join(Venue,Venue.venue_id==Shows.venue_id).filter(Artist.name.ilike('%'+term+'%'))
    return render_template('pages/search_shows.html', results=results, search_term=term)



@app.route('/shows/create',methods=['GET'])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm(request.form)
    body={};
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
