# Restaurant Job Opportunities Feature Documentation

## Overview
The **Restaurant Jobs** feature has been successfully added to the VendorConnect platform, allowing street vendors to explore **career opportunities at restaurants and food chains**. This feature helps vendors transition from street food vending to professional restaurant positions, offering part-time, full-time, and training opportunities.

## 🎯 Purpose
This feature bridges the gap between street food vendors and the organized restaurant industry by:
- **Leveraging existing skills**: Vendors can apply their chaat, dosa, ice cream, tea-making, and other street food skills in restaurant settings
- **Providing career growth**: Transform street vending experience into stable restaurant careers
- **Offering training**: Learn professional cooking standards, hygiene practices, and modern techniques
- **Fixed income opportunities**: Move from variable daily earnings to fixed monthly salaries with benefits

## Features Implemented

### 1. Database Models
- **InternshipOpportunity**: Stores restaurant job listings with details like:
  - Job title, restaurant/company name, detailed description
  - Requirements (focused on practical experience, not formal education)
  - Responsibilities in restaurant environment
  - Skills required (e.g., chaat making, dosa making, tea brewing)
  - Stipend/salary, duration, location, work mode
  - Category (Food Preparation, Beverages, Culinary, etc.)
  - Application deadlines and contact information
  
- **InternshipApplication**: Tracks vendor applications with:
  - Vendor ID, job/internship ID
  - Cover letter describing their street food experience
  - Application status (pending, reviewed, shortlisted, rejected, accepted)
  - Timestamps for tracking

### 2. API Endpoints

#### GET `/api/internships`
- Fetches all active restaurant job opportunities
- Supports filtering by:
  - Category (Food Preparation, Desserts & Beverages, Culinary, etc.)
  - Work mode (on-site primarily, as most restaurant jobs are on-site)
  - Location (city-based)
  - Search query (job title, company name, description)
- Returns application status for logged-in vendors

#### POST `/api/vendor/internship/apply`
- Allows vendors to apply for restaurant positions
- Accepts cover letter where vendors can describe their street food experience
- Prevents duplicate applications
- Validates job availability

#### GET `/api/vendor/internship/applications`
- Returns all job applications for the logged-in vendor
- Includes application status and job details
- Helps vendors track their career opportunities

### 3. User Interface

#### Navigation
- New **"Restaurant Jobs"** menu item in the vendor dashboard sidebar
- Icon: Briefcase (fas fa-briefcase)

#### Restaurant Jobs Section Features
- **Headline**: "Career Opportunities at Restaurants" - Clear messaging about restaurant employment
- **Search & Filters**: 
  - Search by job title/company name
  - Filter by food category (Food Preparation, Beverages, South Indian Cuisine, etc.)
  - Filter by work mode and location
- **Two Tabs**:
  1. **Browse Jobs**: View all available restaurant positions
  2. **My Applications**: Track application status

#### Job Cards Display
- Restaurant/company name and position title
- Work mode badge (mostly on-site for restaurant work)
- Location, salary/stipend, and duration
- Skills required (practical skills like "Chaat Making", "Dosa Making", "Tea Brewing")
- Brief job description
- Action buttons: "Apply Now" and "Details"

#### Detailed Job View Modal
- Complete job description with vendor-friendly language
- Requirements (emphasizes experience over formal education)
- Responsibilities in the restaurant
- Skills required with practical focus
- Salary/stipend information (monthly fixed income)
- Contact information (email, phone, website)
- Application deadline
- Direct apply button

#### Application Management
- Cover letter prompt when applying (vendors can describe their street food experience)
- Application status tracking (pending, reviewed, shortlisted, etc.)
- Visual status indicators with color coding
- Application history with timestamps

### 4. Sample Restaurant Job Opportunities

8 diverse opportunities added for different vendor specializations:

1. **Chaat Counter Assistant** - Paradise Biryani House (Mumbai)
   - For experienced chaat vendors
   - ₹12,000 - ₹18,000 + tips
   - Permanent position opportunity

2. **Ice Cream Station Manager Trainee** - Baskin Robbins India (Delhi)
   - For ice cream vendors
   - ₹15,000 - ₹22,000
   - Full-time position after training

3. **Street Food Section Chef** - Social Offline (Bangalore)
   - For experienced street food vendors
   - ₹18,000 - ₹28,000 + incentives
   - Showcase authentic recipes

4. **Juice Bar Operator** - Naturals Ice Cream & Juice Bar (Pune)
   - For beverage vendors
   - ₹10,000 - ₹16,000
   - Permanent opportunity

5. **Dosa & South Indian Counter Chef** - Saravana Bhavan (Chennai)
   - For dosa makers
   - ₹14,000 - ₹20,000
   - Professional training

6. **Tea & Coffee Station Manager** - Chai Point (Hyderabad)
   - For chai vendors
   - ₹11,000 - ₹17,000
   - Modern techniques training

7. **Samosa & Snacks Production Assistant** - Haldiram's (Nagpur)
   - For samosa/pakora makers
   - ₹13,000 - ₹19,000 + ESI & PF
   - Permanent employment opportunity

8. **Quick Service Restaurant Trainee** - McDonald's India (Multiple Cities)
   - For any food vendor
   - ₹12,000 - ₹18,000 + benefits
   - Complete training program

## Files Modified

### Backend
1. **app.py**
   - Added `InternshipOpportunity` model
   - Added `InternshipApplication` model
   - Added API routes for listing jobs, applying, and tracking applications

2. **add_internship_tables.py** (Migration script)
   - Creates internship tables
   - Adds 8 sample restaurant job opportunities
   - Run with: `python add_internship_tables.py`

### Frontend
3. **templates/vendor_dashboard.html**
   - Added "Restaurant Jobs" navigation menu item
   - Added CSS styles for job cards and UI
   - Added restaurant jobs section HTML with vendor-friendly messaging
   - Added JavaScript functions:
     - `loadInternships()` - Fetch and display jobs
     - `loadMyApplications()` - Load vendor's applications
     - `renderInternships()` - Render job cards
     - `renderMyApplications()` - Render application history
     - `applyForInternship()` - Submit application
     - `showInternshipDetails()` - Show modal with full details
     - `filterInternships()` - Apply search/filter criteria
     - `switchInternshipTab()` - Toggle between browse and applications
   - Updated `showSection()` to include 'Restaurant Job Opportunities' title
   - Updated `loadSectionData()` to call `loadInternships()`

## Usage

### For Street Vendors
1. Login to vendor dashboard
2. Click **"Restaurant Jobs"** in the sidebar
3. Browse available restaurant positions or use filters by category (Chaat, Dosa, Ice Cream, Tea, etc.)
4. Click **"Details"** to view full job information including:
   - What skills from your street food experience are needed
   - What you'll learn in the restaurant
   - Salary and benefits
   - Opportunity for permanent position
5. Click **"Apply Now"** to submit your application
   - Write about your street food experience in the cover letter
   - Describe years of experience, specialties, customer handling skills
6. Switch to **"My Applications"** tab to track your application status
7. Get contacted by restaurant HR for interviews

### Application Cover Letter Tips for Vendors
Vendors should mention:
- Years of street food vending experience
- Specialties (e.g., "Making pani puri for 5 years")
- Customer volume handled daily
- Knowledge of ingredients and preparation
- Any unique recipes or techniques
- Willingness to learn restaurant standards
- Reliability and punctuality

## Styling
- Modern card-based design with hover effects
- Color-coded work mode badges
- Status indicators for applications
- Vendor-friendly language and instructions
- Fully responsive design
- Dark mode support included

## Benefits for Vendors
- **Fixed Income**: Monthly salary instead of variable daily earnings
- **Learning Opportunity**: Professional training and certifications
- **Career Growth**: Path to permanent positions and management roles
- **Social Security**: ESI, PF, and other benefits at some companies
- **Brand Association**: Work with reputable restaurant brands
- **Skill Upgradation**: Learn modern cooking techniques and standards
- **Work-Life Balance**: Fixed shifts instead of long street hours
- **Weather Independence**: Indoor work regardless of weather

## Future Enhancements
- Resume builder for vendors (highlighting street food experience)
- Video profile uploads showing cooking skills
- Skill assessment tests (e.g., "Make pani puri in 5 minutes")
- Admin panel for restaurants to post jobs
- Email/SMS notifications for application status changes
- Interview scheduling system
- Reference system (vendors can refer other vendors)
- Success stories section
- Salary negotiation guidance
- Restaurant ratings by employees

## Testing
1. Ensure database migration has run: `python add_internship_tables.py`
2. Login as a vendor (chaat stall, ice cream vendor, etc.)
3. Navigate to "Restaurant Jobs" section
4. Test browsing, filtering by category (Food Preparation, Beverages, etc.)
5. Apply to relevant positions based on your street food specialty
6. Check "My Applications" tab for submitted applications

## Notes
- All jobs are set to active by default
- Application deadline enforcement is implemented
- Cover letter is optional but **highly recommended** for vendors to describe their experience
- Vendors cannot apply to the same job twice
- Most positions are **on-site** as restaurant work requires physical presence
- Many positions offer **permanent employment** after successful training period
- Vendors can leverage their street food skills for better career opportunities

## Success! 🎉
The restaurant jobs feature is now fully functional and ready to help street vendors discover career opportunities in the organized food industry! This feature can transform lives by providing stable income, professional growth, and dignified employment to hardworking street vendors. 🍜🍦☕

---

**Example Success Story:**
*"Ramesh, a chaat vendor from Mumbai with 10 years experience, applied through VendorConnect and now works as a Chaat Counter Assistant at Paradise Biryani House earning ₹18,000/month + tips. He received professional training, learned hygiene standards, and is now training for a supervisory role!"*

## Features Implemented

### 1. Database Models
- **InternshipOpportunity**: Stores internship listings with details like:
  - Title, company, description
  - Requirements, responsibilities, skills required
  - Stipend, duration, location, work mode (remote/on-site/hybrid)
  - Category, deadlines, contact information
  
- **InternshipApplication**: Tracks vendor applications with:
  - Vendor ID, internship ID
  - Cover letter, resume URL
  - Application status (pending, reviewed, shortlisted, rejected, accepted)
  - Timestamps

### 2. API Endpoints

#### GET `/api/internships`
- Fetches all active internship opportunities
- Supports filtering by:
  - Category (Software Development, Marketing, Design, etc.)
  - Work mode (remote, on-site, hybrid)
  - Location
  - Search query
- Returns application status for logged-in vendors

#### POST `/api/vendor/internship/apply`
- Allows vendors to apply for internships
- Accepts cover letter (optional)
- Prevents duplicate applications
- Validates internship availability

#### GET `/api/vendor/internship/applications`
- Returns all internship applications for the logged-in vendor
- Includes application status and internship details

### 3. User Interface

#### Navigation
- New "Internships" menu item in the vendor dashboard sidebar
- Icon: Briefcase (fas fa-briefcase)

#### Internship Section Features
- **Search & Filters**: Search by title/company, filter by category, work mode, and location
- **Two Tabs**:
  1. **Browse Opportunities**: View all available internships
  2. **My Applications**: Track application status

#### Internship Cards Display
- Company name and position title
- Work mode badge (remote/on-site/hybrid)
- Location, stipend, and duration
- Skills required as tags
- Brief description
- Action buttons: "Apply Now" and "Details"

#### Detailed View Modal
- Complete internship description
- Requirements and responsibilities
- Skills required
- Contact information (email, phone, website)
- Application deadline
- Direct apply button

#### Application Management
- Cover letter prompt when applying
- Application status tracking (pending, reviewed, shortlisted, etc.)
- Visual status indicators
- Application history with timestamps

### 4. Sample Data
8 diverse internship opportunities added across categories:
- Software Development (TechVista Solutions, AppCrafters)
- Digital Marketing (BrandBoost Marketing)
- UI/UX Design (DesignCraft Studio)
- Business Development (GrowthHub Ventures)
- Data Science (DataMinds Analytics)
- Content Writing (WordCraft Media)
- Human Resources (PeopleFirst HR Solutions)

## Files Modified

### Backend
1. **app.py**
   - Added `InternshipOpportunity` model (line ~990)
   - Added `InternshipApplication` model (line ~1023)
   - Added API routes (after line ~3286):
     - `/api/internships` - List internships
     - `/api/vendor/internship/apply` - Apply for internship
     - `/api/vendor/internship/applications` - Get vendor applications

2. **add_internship_tables.py** (New file)
   - Migration script to create tables
   - Adds 8 sample internship opportunities
   - Run with: `python add_internship_tables.py`

### Frontend
3. **templates/vendor_dashboard.html**
   - Added navigation menu item (line ~1849)
   - Added CSS styles for internship cards and UI (line ~1774)
   - Added internship section HTML (line ~2404)
   - Added JavaScript functions (line ~4253):
     - `loadInternships()` - Fetch and display internships
     - `loadMyApplications()` - Load vendor's applications
     - `renderInternships()` - Render internship cards
     - `renderMyApplications()` - Render application history
     - `applyForInternship()` - Submit application
     - `showInternshipDetails()` - Show modal with full details
     - `filterInternships()` - Apply search/filter criteria
     - `switchInternshipTab()` - Toggle between browse and applications
   - Updated `showSection()` to include 'internships' title (line ~3118)
   - Updated `loadSectionData()` to call `loadInternships()` (line ~3172)

## Usage

### For Vendors
1. Login to vendor dashboard
2. Click "Internships" in the sidebar
3. Browse available opportunities or use filters
4. Click "Details" to view full information
5. Click "Apply Now" to submit application (optional cover letter)
6. Switch to "My Applications" tab to track status

### For Administrators
To add new internship opportunities, insert into the `internship_opportunity` table or create a management interface.

## Styling
- Modern card-based design with hover effects
- Color-coded work mode badges (green for remote, orange for on-site, blue for hybrid)
- Status indicators for applications (yellow for pending, green for accepted, etc.)
- Fully responsive design
- Dark mode support included

## Future Enhancements
- Resume upload functionality
- Admin panel for managing internships
- Email notifications for application status changes
- Application analytics dashboard
- Company profiles
- Advanced search with salary range filters
- Saved/bookmarked internships
- Application withdrawal option

## Testing
1. Ensure database migration has run: `python add_internship_tables.py`
2. Login as a vendor
3. Navigate to Internships section
4. Test browsing, filtering, and applying
5. Check "My Applications" tab for submitted applications

## Notes
- All internships are set to active by default
- Application deadline enforcement is implemented on the backend
- Cover letter is optional but recommended
- Vendors cannot apply to the same internship twice
- The feature integrates seamlessly with the existing vendor dashboard

## Success! 🎉
The internship feature is now fully functional and ready to help vendors discover and apply for career opportunities!
