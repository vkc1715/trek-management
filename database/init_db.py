from models import db, User, Trek
from datetime import date, timedelta

def seed_data():
    # Add realistic seed data for 10 Indian trekking routes if database is empty
    if Trek.query.count() == 0:
        treks = [
            Trek(
                trek_name='Kedarkantha Trek',
                location='Uttarkashi, Uttarakhand',
                difficulty='Easy',
                duration_days=6,
                available_slots=30,
                description='One of India\'s most popular winter treks, known for snow-covered trails, pine forests, and panoramic Himalayan summit views.',
                status='Open',
                start_date=date.today() + timedelta(days=15),
                end_date=date.today() + timedelta(days=21),
                trek_image='https://images.unsplash.com/photo-1544198365-f5d60b6d8190?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Valley of Flowers Trek',
                location='Chamoli, Uttarakhand',
                difficulty='Easy',
                duration_days=5,
                available_slots=35,
                description='UNESCO World Heritage Site famous for vibrant alpine flowers, waterfalls, and stunning mountain scenery.',
                status='Open',
                start_date=date.today() + timedelta(days=20),
                end_date=date.today() + timedelta(days=25),
                trek_image='https://images.unsplash.com/photo-1596767663459-bc1ee92215c7?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Hampta Pass Trek',
                location='Kullu to Spiti, Himachal Pradesh',
                difficulty='Moderate',
                duration_days=5,
                available_slots=25,
                description='A dramatic crossover trek connecting the lush Kullu Valley with the barren landscapes of Spiti.',
                status='Open',
                start_date=date.today() + timedelta(days=25),
                end_date=date.today() + timedelta(days=30),
                trek_image='https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Brahmatal Trek',
                location='Chamoli, Uttarakhand',
                difficulty='Moderate',
                duration_days=6,
                available_slots=30,
                description='A winter trek offering frozen lakes, snow-covered forests, and magnificent Himalayan views.',
                status='Open',
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=36),
                trek_image='https://images.unsplash.com/photo-1522163182402-834f871fd851?q=80&w=2062&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Sandakphu Trek',
                location='Darjeeling District, West Bengal',
                difficulty='Moderate',
                duration_days=7,
                available_slots=25,
                description='Famous for panoramic views of Everest, Kanchenjunga, Lhotse, and Makalu.',
                status='Open',
                start_date=date.today() + timedelta(days=35),
                end_date=date.today() + timedelta(days=42),
                trek_image='https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Rupin Pass Trek',
                location='Himachal Pradesh to Uttarakhand',
                difficulty='Hard',
                duration_days=8,
                available_slots=20,
                description='Known for hanging villages, waterfalls, snow bridges, and dramatic mountain terrain.',
                status='Open',
                start_date=date.today() + timedelta(days=40),
                end_date=date.today() + timedelta(days=48),
                trek_image='https://images.unsplash.com/photo-1551632811-561732d1e306?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Goechala Trek',
                location='West Sikkim, Sikkim',
                difficulty='Hard',
                duration_days=10,
                available_slots=20,
                description='One of India\'s most scenic treks, offering breathtaking views of Kanchenjunga and surrounding Himalayan peaks.',
                status='Open',
                start_date=date.today() + timedelta(days=45),
                end_date=date.today() + timedelta(days=55),
                trek_image='https://images.unsplash.com/photo-1588714477688-cf1694db09ee?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Tarsar Marsar Trek',
                location='Anantnag, Jammu & Kashmir',
                difficulty='Moderate',
                duration_days=7,
                available_slots=20,
                description='A beautiful alpine-lake trek through meadows, valleys, and pristine mountain landscapes.',
                status='Open',
                start_date=date.today() + timedelta(days=50),
                end_date=date.today() + timedelta(days=57),
                trek_image='https://images.unsplash.com/photo-1595815771614-ade9d652a65d?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Kashmir Great Lakes Trek',
                location='Ganderbal, Jammu & Kashmir',
                difficulty='Hard',
                duration_days=8,
                available_slots=18,
                description='Features multiple alpine lakes, high-altitude meadows, and some of the most spectacular scenery in India.',
                status='Open',
                start_date=date.today() + timedelta(days=55),
                end_date=date.today() + timedelta(days=63),
                trek_image='https://images.unsplash.com/photo-1601614917637-29ab55694d0c?q=80&w=2070&auto=format&fit=crop'
            ),
            Trek(
                trek_name='Kuari Pass Trek',
                location='Chamoli, Uttarakhand',
                difficulty='Moderate',
                duration_days=6,
                available_slots=25,
                description='Historic trail associated with Lord Curzon, offering excellent Himalayan mountain views.',
                status='Open',
                start_date=date.today() + timedelta(days=60),
                end_date=date.today() + timedelta(days=66),
                trek_image='https://images.unsplash.com/photo-1506197061617-7f5c0b093236?q=80&w=2070&auto=format&fit=crop'
            )
        ]
        
        for trek in treks:
            db.session.add(trek)
            
        db.session.commit()
        print("Realistic Indian treks seeded successfully.")

def initialize_database():
    # Automatically create default admin if not exists
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(
            full_name='Admin User',
            email='admin@gmail.com',
            phone='1234567890',
            role='admin'
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created.")

    # Call seed_data to populate treks
    seed_data()
