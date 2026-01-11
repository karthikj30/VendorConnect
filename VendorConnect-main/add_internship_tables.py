#!/usr/bin/env python3
"""
Migration script to add internship tables to the database
"""

from app import app, db, InternshipOpportunity, InternshipApplication
from datetime import datetime, timedelta

def add_internship_tables():
    """Add internship opportunity and application tables"""
    
    with app.app_context():
        # Create tables
        print("Creating internship tables...")
        db.create_all()
        print("✅ Internship tables created successfully!")
        
        # Add sample internship opportunities for street vendors at restaurants
        print("\nAdding sample internship opportunities...")
        
        sample_internships = [
            {
                'title': 'Chaat Counter Assistant - Part Time',
                'company': 'Paradise Biryani House',
                'description': 'Great opportunity for experienced chaat vendors to work in our popular restaurant chain. Learn standardized recipes, hygiene practices, and customer service at scale.',
                'requirements': '• Experience in making chaat items (pani puri, bhel, sev puri)\n• Basic understanding of food hygiene\n• Ability to work in fast-paced environment\n• No formal education required',
                'responsibilities': '• Prepare chaat items as per restaurant standards\n• Maintain cleanliness and hygiene\n• Serve customers with a smile\n• Learn new recipes and techniques',
                'skills_required': 'Chaat Making, Customer Service, Fast Hands, Hygiene Awareness',
                'stipend': '₹12,000 - ₹18,000 per month + Tips',
                'duration': '3-6 months (with permanent position opportunity)',
                'location': 'Mumbai, Maharashtra',
                'work_mode': 'on-site',
                'category': 'Food Preparation',
                'application_deadline': datetime.utcnow() + timedelta(days=30),
                'contact_email': 'jobs@paradisebiryani.com',
                'contact_phone': '+91-9876543210',
                'company_website': 'https://www.paradisebiryani.com',
                'is_active': True
            },
            {
                'title': 'Ice Cream Station Manager Trainee',
                'company': 'Baskin Robbins India',
                'description': 'Transform your ice cream stall experience into a career! Learn modern ice cream making, inventory management, and customer service from industry experts.',
                'requirements': '• Experience in ice cream making or selling\n• Passion for desserts and sweets\n• Good communication skills\n• Willing to learn and grow',
                'responsibilities': '• Manage ice cream station operations\n• Learn flavor creation and mixing\n• Handle customer orders efficiently\n• Maintain quality standards\n• Assist in inventory management',
                'skills_required': 'Ice Cream Making, Customer Interaction, Quick Service, Enthusiasm',
                'stipend': '₹15,000 - ₹22,000 per month',
                'duration': '6 months (Full-time position after training)',
                'location': 'Delhi NCR',
                'work_mode': 'on-site',
                'category': 'Desserts & Beverages',
                'application_deadline': datetime.utcnow() + timedelta(days=20),
                'contact_email': 'careers@baskinrobbins.in',
                'contact_phone': '+91-9876543211',
                'company_website': 'https://www.baskinrobbinsindia.com',
                'is_active': True
            },
            {
                'title': 'Street Food Section Chef - Training Program',
                'company': 'Social Offline',
                'description': 'Bring your authentic street food skills to our trendy restaurant! We are looking for experienced street vendors to join our kitchen team and showcase traditional recipes.',
                'requirements': '• 2+ years experience in street food vending\n• Expertise in regional street foods\n• Authentic cooking style\n• Food safety awareness',
                'responsibilities': '• Prepare authentic street food dishes\n• Train kitchen staff on traditional methods\n• Maintain consistency and quality\n• Create new menu items\n• Ensure food safety standards',
                'skills_required': 'Street Food Cooking, Regional Cuisine, Authentic Recipes, Teamwork',
                'stipend': '₹18,000 - ₹28,000 per month + Incentives',
                'duration': '4-6 months',
                'location': 'Bangalore, Karnataka',
                'work_mode': 'on-site',
                'category': 'Culinary',
                'application_deadline': datetime.utcnow() + timedelta(days=25),
                'contact_email': 'careers@socialoffline.in',
                'contact_phone': '+91-9876543212',
                'company_website': 'https://www.socialoffline.in',
                'is_active': True
            },
            {
                'title': 'Juice Bar Operator - Full Time',
                'company': 'Naturals Ice Cream & Juice Bar',
                'description': 'Join our growing juice bar chain! Learn professional juice making, fruit handling, and customer service. Perfect for vendors with beverage experience.',
                'requirements': '• Experience in making fresh juices or beverages\n• Knowledge of fruits and their preparation\n• Customer-friendly attitude\n• Basic math skills for billing',
                'responsibilities': '• Prepare fresh juices and smoothies\n• Handle fruit inventory\n• Serve customers efficiently\n• Maintain cleanliness standards\n• Learn new recipes and combinations',
                'skills_required': 'Juice Making, Fruit Knowledge, Customer Service, Hygiene',
                'stipend': '₹10,000 - ₹16,000 per month',
                'duration': '3 months (Permanent opportunity)',
                'location': 'Pune, Maharashtra',
                'work_mode': 'on-site',
                'category': 'Beverages',
                'application_deadline': datetime.utcnow() + timedelta(days=15),
                'contact_email': 'hr@naturals.co.in',
                'contact_phone': '+91-9876543213',
                'company_website': 'https://www.naturals.in',
                'is_active': True
            },
            {
                'title': 'Dosa & South Indian Counter Chef',
                'company': 'Saravana Bhavan',
                'description': 'Excellent opportunity for experienced dosa makers! Join our famous restaurant chain and upgrade your skills with professional training and fixed income.',
                'requirements': '• Expert in making dosas, idlis, vadas\n• Knowledge of South Indian cuisine\n• Fast and efficient work style\n• Clean working habits',
                'responsibilities': '• Prepare various types of dosas\n• Maintain batter quality\n• Ensure portion control\n• Keep work area clean\n• Learn new South Indian dishes',
                'skills_required': 'Dosa Making, South Indian Cooking, Speed, Quality Control',
                'stipend': '₹14,000 - ₹20,000 per month',
                'duration': '6 months',
                'location': 'Chennai, Tamil Nadu',
                'work_mode': 'on-site',
                'category': 'South Indian Cuisine',
                'application_deadline': datetime.utcnow() + timedelta(days=40),
                'contact_email': 'jobs@saravanabhavan.com',
                'contact_phone': '+91-9876543214',
                'company_website': 'https://www.saravanabhavan.com',
                'is_active': True
            },
            {
                'title': 'Tea & Coffee Station Manager',
                'company': 'Chai Point',
                'description': 'Turn your chai stall expertise into a career! We train vendors in professional tea and coffee making, customer service, and business operations.',
                'requirements': '• Experience in tea/coffee making\n• Passion for beverages\n• Good communication skills\n• Willing to learn modern techniques',
                'responsibilities': '• Prepare various types of chai and coffee\n• Manage beverage station\n• Serve customers professionally\n• Maintain quality standards\n• Handle cash and billing',
                'skills_required': 'Tea Making, Coffee Brewing, Customer Service, Cash Handling',
                'stipend': '₹11,000 - ₹17,000 per month',
                'duration': '3 months',
                'location': 'Hyderabad, Telangana',
                'work_mode': 'on-site',
                'category': 'Beverages',
                'application_deadline': datetime.utcnow() + timedelta(days=35),
                'contact_email': 'careers@chaipoint.com',
                'contact_phone': '+91-9876543215',
                'company_website': 'https://www.chaipoint.com',
                'is_active': True
            },
            {
                'title': 'Samosa & Snacks Production Assistant',
                'company': 'Haldiram\'s Manufacturing Unit',
                'description': 'Join India\'s leading snacks brand! Learn industrial food production while bringing your traditional samosa-making skills to our facility.',
                'requirements': '• Experience in making samosas or pakoras\n• Understanding of fried snacks\n• Ability to work in production environment\n• Physically fit for standing work',
                'responsibilities': '• Prepare samosas and snacks at scale\n• Follow standardized recipes\n• Maintain quality control\n• Work as part of production team\n• Learn modern food production methods',
                'skills_required': 'Samosa Making, Frying Skills, Quality Awareness, Teamwork',
                'stipend': '₹13,000 - ₹19,000 per month + ESI & PF',
                'duration': '6 months (Permanent employment opportunity)',
                'location': 'Nagpur, Maharashtra',
                'work_mode': 'on-site',
                'category': 'Food Production',
                'application_deadline': datetime.utcnow() + timedelta(days=28),
                'contact_email': 'recruitment@haldirams.com',
                'contact_phone': '+91-9876543216',
                'company_website': 'https://www.haldirams.com',
                'is_active': True
            },
            {
                'title': 'Quick Service Restaurant - Multi-Skill Trainee',
                'company': 'McDonald\'s India',
                'description': 'Complete training program for street food vendors! Learn international standards, food safety, customer service, and get certified skills for a bright future.',
                'requirements': '• Any food vending experience welcome\n• Age 18-40 years\n• Basic Hindi/English communication\n• Enthusiastic and hardworking',
                'responsibilities': '• Learn multiple station operations\n• Master food preparation standards\n• Understand hygiene and safety protocols\n• Provide excellent customer service\n• Work flexible shifts',
                'skills_required': 'Food Preparation, Customer Service, Teamwork, Flexibility',
                'stipend': '₹12,000 - ₹18,000 per month + Benefits',
                'duration': '4 months (Career advancement opportunities)',
                'location': 'Multiple Cities (Mumbai, Delhi, Bangalore)',
                'work_mode': 'on-site',
                'category': 'Quick Service Restaurant',
                'application_deadline': datetime.utcnow() + timedelta(days=18),
                'contact_email': 'careers@mcdonaldsindia.com',
                'contact_phone': '+91-9876543217',
                'company_website': 'https://www.mcdonaldsindia.com',
                'is_active': True
            }
        ]
        
        for internship_data in sample_internships:
            existing = InternshipOpportunity.query.filter_by(
                title=internship_data['title'],
                company=internship_data['company']
            ).first()
            
            if not existing:
                internship = InternshipOpportunity(**internship_data)
                db.session.add(internship)
                print(f"  ✅ Added: {internship_data['title']} at {internship_data['company']}")
            else:
                print(f"  ⏭️  Skipped (already exists): {internship_data['title']} at {internship_data['company']}")
        
        db.session.commit()
        print("\n✅ All done! Internship tables and sample data added successfully.")

if __name__ == '__main__':
    add_internship_tables()
