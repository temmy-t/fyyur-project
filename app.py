#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
with app.app_context():
    db.create_all()
migrate = Migrate(app, db)
# app.register_blueprint(routes)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    venue = db.session.query(Venue).order_by(db.desc(Venue.id)).limit(10)
    artist = db.session.query(Artist).order_by(db.desc(Artist.id)).limit(10)
    return render_template('pages/home.html', venues=venue, artists=artist)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    results = db.session.query(Venue.city, Venue.state).distinct(
        Venue.city, Venue.state).all()
    for result in results:
        location = {
            "state": result.state,
            "city": result.city
        }
        venues = Venue.query.filter_by(
            city=result.city, state=result.state).all()

        # format each venue
        grouped_venues = []
        for venue in venues:
            grouped_venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
            })

        location["venues"] = grouped_venues
        data.append(location)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search = '%' + request.form['search_term'] + '%'
    venues = Venue.query.filter(Venue.name.ilike(search))
    data = []
    for venue in venues:
        data.append({
            "id": venue.id,
            "name": venue.name
        })
    response = {
        "count": venues.count(),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    past_show = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id, Show.start_time < datetime.now())
    past_shows = []
    for show in past_show:
        past_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })

    upcoming_show = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id, Show.start_time >= datetime.now())
    upcoming_shows = []
    for show in upcoming_show:
        upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })

    venue = Venue.query.get(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()
    if form.validate_on_submit():
        new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            genres=','.join(form.genres.data),
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
        )
        try:
            db.session.add(new_venue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            db.session.rollback()
            flash('Venue ' + request.form['name'] +
                  ' was not successfully listed!')
        finally:
            db.session.close()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    else:
        for error_message in form.errors.values():
            flash(f'An error occurred on {error_message[0]}, Venue ' +
                  request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        Show.query.filter_by(venue_id=venue_id).delete()
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search = '%' + request.form['search_term'] + '%'
    artists = Artist.query.filter(Artist.name.ilike(search))
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    response = {
        "count": artists.count(),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    past_show = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time < datetime.now())
    past_shows = []
    for show in past_show:
        past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })

    upcoming_show = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time >= datetime.now())
    upcoming_shows = []
    for show in upcoming_show:
        upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })

    artist = Artist.query.get(artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "genres": artist.genres.split(','),
        "website_link": artist.website_link,
        "image_link": artist.image_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
    }
    form = ArtistForm(data=artist_data)

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    if form.validate_on_submit():
        artist_update = Artist.query.get(artist_id)
        artist_update.name = form.name.data
        artist_update.city = form.city.data
        artist_update.state = form.state.data
        artist_update.phone = form.phone.data
        artist_update.facebook_link = form.facebook_link.data
        artist_update.genres = ','.join(form.genres.data)
        artist_update.website_link = form.website_link.data
        artist_update.image_link = form.image_link.data
        artist_update.seeking_venue = form.seeking_venue.data
        artist_update.seeking_description = form.seeking_description.data
        try:
            db.session.commit()
            flash('Artist ' + artist_update.name + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('Artist ' + form.name.data + ' was not successfully updated!')
        finally:
            db.session.close()
    else:
        for error_message in form.errors.values():
            flash(f'An error occurred on {error_message[0]}, Artist ' +
                  request.form['name'] + ' could not be listed.')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    form = VenueForm(data=venue_data)

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm()
    if form.validate_on_submit():
        venue_update = Venue.query.get(venue_id)
        venue_update.name = form.name.data
        venue_update.city = form.city.data
        venue_update.state = form.state.data
        venue_update.phone = form.phone.data
        venue_update.facebook_link = form.facebook_link.data
        venue_update.genres = ','.join(form.genres.data)
        venue_update.website_link = form.website_link.data
        venue_update.image_link = form.image_link.data
        venue_update.seeking_talent = form.seeking_talent.data
        venue_update.seeking_description = form.seeking_description.data
        try:
            db.session.commit()
            flash('Venue ' + venue_update.name + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('Venue ' + form.name.data + ' was not successfully updated!')
        finally:
            db.session.close()
    else:
        for error_message in form.errors.values():
            flash(f'An error occurred on {error_message[0]}, Venue ' +
                  request.form['name'] + ' could not be listed.')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm()
    if form.validate_on_submit():
        new_artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            facebook_link=form.facebook_link.data,
            genres=','.join(form.genres.data),
            website_link=form.website_link.data,
            image_link=form.image_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data,
        )
        try:
            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            db.session.rollback()
            flash('Artist ' + request.form['name'] +
                  ' was not successfully listed!')
        finally:
            db.session.close()
        # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    else:
        for error_message in form.errors.values():
            flash(f'An error occurred on {error_message[0]}, Artist ' +
                  request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')


@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        Show.query.filter_by(artist_id=artist_id).delete()
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = Show.query.all()
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    if form.validate_on_submit():
        if Venue.query.get(request.form['venue_id']) and Artist.query.get(request.form['artist_id']):
            new_show = Show(
                venue_id=form.venue_id.data,
                artist_id=form.artist_id.data,
                start_time=form.start_time.data
            )
            try:
                db.session.add(new_show)
                db.session.commit()
                flash('Show was successfully listed!')
            except:
                db.session.rollback()
                flash('Show was not successfully listed!')
            finally:
                db.session.close()
        else:
            flash(
                "An error occurred. the provided IDs don't exist, Show could not be listed.")
            return render_template('forms/new_show.html')
    else:
        for error_message in form.errors.values():
            flash(f'An error occurred on {error_message[0]}, Show ' +
                  request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
