import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date

# Page configuration
st.set_page_config(
    page_title="Book Tracker", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS FOR PROFESSIONAL LOOK ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main > div {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        backdrop-filter: blur(10px);
    }
    
    .modern-card {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
        margin-bottom: 1rem;
        border: 1px solid #f0f0f0;
    }
    
    .modern-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        border-color: #e0e0e0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.25rem 0;
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.9;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px;
    }
    
    .badge-gold { background: linear-gradient(135deg, #f5af19 0%, #f12711 100%); color: white; }
    .badge-silver { background: linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%); color: white; }
    .badge-bronze { background: linear-gradient(135deg, #cd7f32 0%, #8b4513 100%); color: white; }
    .badge-blue { background: #667eea; color: white; }
    .badge-gray { background: #e0e0e0; color: #666; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-size: 0.875rem;
    }
    
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.3px;
    }
    
    h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .rating-stars {
        color: #fbbf24;
        font-size: 0.875rem;
        letter-spacing: 1px;
    }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e0e0e0, transparent);
        margin: 1.5rem 0;
    }
    
    .status-read {
        color: #10b981;
        font-weight: 500;
    }
    
    .status-unread {
        color: #ef4444;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize data files
DATA_FILE = "books.csv"
REVIEWS_FILE = "reviews.json"

def load_books():
    """Load books from CSV file"""
    required_columns = ["book_number", "series", "title", "author", "is_read", "format", "date_added", "date_finished"]
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        for col in required_columns:
            if col not in df.columns:
                if col == "is_read":
                    df[col] = "N"
                elif col in ["date_added", "date_finished"]:
                    df[col] = ""
                else:
                    df[col] = ""
        
        df['title'] = df['title'].fillna('Unknown Title')
        df['author'] = df['author'].fillna('Unknown Author')
        df['format'] = df['format'].fillna('Unknown')
        
        if 'date_added' not in df.columns or df['date_added'].isna().all():
            df['date_added'] = datetime.now().strftime('%Y-%m-%d')
        
        def convert_is_read(value):
            if pd.isna(value):
                return False
            value_str = str(value).upper().strip()
            return value_str in ['Y', 'YES', 'TRUE', '1', 'READ']
        
        df['is_read'] = df['is_read'].apply(convert_is_read)
        return df
    else:
        return pd.DataFrame(columns=required_columns)

def load_reviews():
    """Load book reviews and ratings"""
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_reviews(reviews):
    """Save book reviews"""
    with open(REVIEWS_FILE, 'w') as f:
        json.dump(reviews, f)

def save_books(df):
    """Save books to CSV"""
    df_to_save = df.copy()
    df_to_save['is_read'] = df_to_save['is_read'].map({True: 'Y', False: 'N'})
    df_to_save.to_csv(DATA_FILE, index=False)

# Load data
df = load_books()
reviews = load_reviews()

# Sidebar
with st.sidebar:
    st.markdown('<h2 style="text-align: center; margin-bottom: 0;">Book Tracker</h2>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; font-size: 0.8rem;">Personal Library Management</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["Dashboard", "Add Book", "Update Status", "Rate & Review", "Insights", "Achievements", "Library"]
    )
    
    st.markdown("---")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==================== PAGE 1: DASHBOARD ====================
if page == "Dashboard":
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Overview of your reading journey</p>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.info("Your library is empty. Start by adding your first book.")
    else:
        total_books = len(df)
        books_read = len(df[df['is_read'] == True])
        books_unread = total_books - books_read
        read_percentage = (books_read / total_books * 100) if total_books > 0 else 0
        
        # Calculate reading streak
        read_dates = []
        if 'date_finished' in df.columns:
            for _, book in df[df['is_read'] == True].iterrows():
                if 'date_finished' in book and pd.notna(book['date_finished']) and book['date_finished']:
                    try:
                        if isinstance(book['date_finished'], str):
                            date_obj = pd.to_datetime(book['date_finished']).date()
                        else:
                            date_obj = book['date_finished'].date() if hasattr(book['date_finished'], 'date') else book['date_finished']
                        read_dates.append(date_obj)
                    except:
                        pass
        
        current_streak = 0
        if read_dates:
            read_dates = sorted(set(read_dates))
            today = date.today()
            check_date = today
            while check_date in read_dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Books</div>
                    <div class="metric-value">{total_books}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Books Read</div>
                    <div class="metric-value">{books_read}</div>
                    <div style="font-size: 0.7rem;">{read_percentage:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">To Be Read</div>
                    <div class="metric-value">{books_unread}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_rating = sum(reviews.values()) / len(reviews) if reviews else 0
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Average Rating</div>
                    <div class="metric-value">{avg_rating:.1f}</div>
                    <div class="rating-stars">{'★' * int(avg_rating)}{'☆' * (5 - int(avg_rating))}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Current Streak</div>
                    <div class="metric-value">{current_streak}</div>
                    <div style="font-size: 0.7rem;">days</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<h3>Recent Additions</h3>", unsafe_allow_html=True)
            recent = df.sort_values('date_added', ascending=False).head(5)
            for _, book in recent.iterrows():
                status_class = "status-read" if book['is_read'] else "status-unread"
                status_text = "Read" if book['is_read'] else "To Read"
                st.markdown(f"""
                    <div class="modern-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{book['title']}</strong>
                                <div style="color: #666; font-size: 0.8rem;">{book['author']}</div>
                            </div>
                            <div class="{status_class}">{status_text}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3>Quick Actions</h3>", unsafe_allow_html=True)
            if st.button("Add New Book", use_container_width=True):
                st.session_state.page = "Add Book"
                st.rerun()
            if st.button("Rate a Book", use_container_width=True):
                st.session_state.page = "Rate & Review"
                st.rerun()

# ==================== PAGE 2: ADD BOOK ====================
elif page == "Add Book":
    st.markdown("<h1>Add New Book</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Expand your library collection</p>', unsafe_allow_html=True)
    
    with st.form("add_book_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title *", placeholder="Book title")
            author = st.text_input("Author *", placeholder="Author name")
            series = st.text_input("Series", placeholder="Series name (optional)")
        
        with col2:
            book_number = st.text_input("Book Number", placeholder="e.g., 1, 2, 3")
            format_options = ["Kindle", "Paperback", "Hardcover", "Audio", "PDF", "Other"]
            format_type = st.selectbox("Format", format_options)
            is_read = st.checkbox("Mark as read")
            date_finished = None
            if is_read:
                date_finished = st.date_input("Date finished", datetime.now())
        
        submitted = st.form_submit_button("Add to Library", use_container_width=True)
        
        if submitted and title and author:
            new_book = pd.DataFrame([{
                "book_number": book_number or "",
                "series": series or "",
                "title": title,
                "author": author,
                "is_read": is_read,
                "format": format_type,
                "date_added": datetime.now().strftime('%Y-%m-%d'),
                "date_finished": date_finished.strftime('%Y-%m-%d') if date_finished else ""
            }])
            df = pd.concat([df, new_book], ignore_index=True)
            save_books(df)
            st.success(f"'{title}' has been added to your library.")
            st.balloons()

# ==================== PAGE 3: UPDATE STATUS ====================
elif page == "Update Status":
    st.markdown("<h1>Update Reading Status</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Track your reading progress</p>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.info("No books in your library. Add some first.")
    else:
        search = st.text_input("Search books", placeholder="Title or author...")
        
        filtered = df[df['title'].str.contains(search, case=False, na=False) | 
                     df['author'].str.contains(search, case=False, na=False)] if search else df
        
        if len(filtered) == 0:
            st.warning("No books found")
        else:
            book_options = filtered.apply(lambda x: f"{x['title']} - {x['author']}", axis=1).tolist()
            selected = st.selectbox("Select a book", book_options)
            selected_book = filtered.iloc[book_options.index(selected)]
            
            col1, col2 = st.columns(2)
            with col1:
                current_status = "Read" if selected_book['is_read'] else "Not Read"
                st.markdown(f"**Current Status:** {current_status}")
                st.markdown(f"**Author:** {selected_book['author']}")
                st.markdown(f"**Format:** {selected_book['format']}")
            with col2:
                new_status = st.radio("Update to:", ["Read", "Not Read"], horizontal=True)
                date_finished = None
                if new_status == "Read":
                    date_finished = st.date_input("Date finished", datetime.now())
                
                if st.button("Update Status", use_container_width=True):
                    idx = df[df['title'] == selected_book['title']].index[0]
                    df.at[idx, 'is_read'] = (new_status == "Read")
                    if date_finished:
                        df.at[idx, 'date_finished'] = date_finished.strftime('%Y-%m-%d')
                    save_books(df)
                    st.success(f"'{selected_book['title']}' status updated.")

# ==================== PAGE 4: RATE & REVIEW ====================
elif page == "Rate & Review":
    st.markdown("<h1>Rate & Review</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Share your thoughts on books you\'ve read</p>', unsafe_allow_html=True)
    
    read_books = df[df['is_read'] == True]
    
    if len(read_books) == 0:
        st.info("You haven't read any books yet. Mark some as read first.")
    else:
        book_options = read_books.apply(lambda x: f"{x['title']} by {x['author']}", axis=1).tolist()
        selected = st.selectbox("Select a book", book_options)
        selected_book = read_books.iloc[book_options.index(selected)]
        book_key = f"{selected_book['title']}_{selected_book['author']}"
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            current_rating = reviews.get(book_key, 0)
            rating = st.slider("Rating (1-5)", 1, 5, int(current_rating) if current_rating else 3)
            st.markdown(f'<div class="rating-stars">{"★" * rating}{"☆" * (5-rating)}</div>', unsafe_allow_html=True)
        
        with col2:
            review_text = st.text_area("Review (optional)", placeholder="What did you think about this book?")
        
        if st.button("Save Rating", use_container_width=True):
            reviews[book_key] = rating
            if review_text:
                reviews[f"{book_key}_review"] = review_text
            save_reviews(reviews)
            st.success(f"Rated {rating}/5 stars for '{selected_book['title']}'.")
            st.balloons()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("<h3>Recent Reviews</h3>", unsafe_allow_html=True)
        rated_books = [(k, v) for k, v in reviews.items() if not k.endswith('_review')]
        for book_key, rating in list(rated_books)[:5]:
            title, author = book_key.split('_', 1)
            review = reviews.get(f"{book_key}_review", "")
            st.markdown(f"""
                <div class="modern-card">
                    <strong>{title}</strong><br>
                    <span style="color: #666; font-size: 0.8rem;">by {author}</span>
                    <div class="rating-stars">{"★" * rating}{"☆" * (5-rating)}</div>
                    {f'<span style="color: #666; font-size: 0.8rem;">{review[:100]}...</span>' if review else ""}
                </div>
            """, unsafe_allow_html=True)

# ==================== PAGE 5: INSIGHTS ====================
elif page == "Insights":
    st.markdown("<h1>Reading Insights</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Analytics and statistics</p>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.info("Add books to see insights.")
    else:
        total = len(df)
        read = len(df[df['is_read'] == True])
        
        # Reading progress over time
        df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
        df_clean = df.dropna(subset=['date_added'])
        
        if len(df_clean) > 0:
            monthly = df_clean.set_index('date_added').resample('ME').size()
        else:
            monthly = pd.Series()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.pie(values=[read, total-read], names=['Read', 'Unread'], 
                         title='Reading Progress', hole=0.4,
                         color_discrete_sequence=['#667eea', '#e0e0e0'])
            fig1.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            if len(monthly) > 0:
                fig2 = px.line(x=monthly.index, y=monthly.values, 
                              title='Books Added Over Time',
                              labels={'x': 'Month', 'y': 'Books Added'})
                fig2.update_traces(line_color='#667eea', line_width=3)
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Not enough date data to show timeline.")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Author stats
        st.markdown("<h3>Top Authors</h3>", unsafe_allow_html=True)
        top_authors = df['author'].value_counts().head(10)
        fig3 = px.bar(x=top_authors.values, y=top_authors.index, orientation='h',
                     title='Most Collected Authors')
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Format distribution
        st.markdown("<h3>Format Distribution</h3>", unsafe_allow_html=True)
        format_counts = df['format'].value_counts()
        fig4 = px.pie(values=format_counts.values, names=format_counts.index,
                     title='Books by Format', hole=0.3)
        st.plotly_chart(fig4, use_container_width=True)
        
        # Reading goals
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("<h3>Reading Goals</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            yearly_goal = st.number_input("Yearly Goal", min_value=1, max_value=500, value=50)
            progress = min(read / yearly_goal, 1.0) if yearly_goal > 0 else 0
            st.progress(progress)
            st.caption(f"{read} of {yearly_goal} books ({read/yearly_goal*100:.1f}%)")
        
        with col2:
            monthly_goal = st.number_input("Monthly Goal", min_value=1, max_value=50, value=5)
            current_month = datetime.now().month
            if 'date_finished' in df.columns:
                df['date_finished'] = pd.to_datetime(df['date_finished'], errors='coerce')
                monthly_read = len(df[(df['is_read'] == True) & (df['date_finished'].dt.month == current_month)])
            else:
                monthly_read = 0
            monthly_progress = min(monthly_read / monthly_goal, 1.0) if monthly_goal > 0 else 0
            st.progress(monthly_progress)
            st.caption(f"{monthly_read} of {monthly_goal} books this month")
        
        with col3:
            days_in_year = (datetime.now() - datetime(datetime.now().year, 1, 1)).days + 1
            pace = (read / days_in_year) * 365 if days_in_year > 0 else 0
            st.metric("Projected Year End", f"{pace:.0f} books")

# ==================== PAGE 6: ACHIEVEMENTS ====================
elif page == "Achievements":
    st.markdown("<h1>Achievements</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Your reading milestones</p>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.info("Start reading to earn achievements.")
    else:
        read_books = len(df[df['is_read'] == True])
        avg_rating = sum(reviews.values()) / len(reviews) if reviews else 0
        unique_authors = df['author'].nunique()
        
        # Define achievements
        achievements = []
        
        if read_books >= 1:
            achievements.append(("First Book", "You read your first book", "badge-bronze"))
        if read_books >= 10:
            achievements.append(("Novice Reader", "Read 10 books", "badge-bronze"))
        if read_books >= 25:
            achievements.append(("Avid Reader", "Read 25 books", "badge-silver"))
        if read_books >= 50:
            achievements.append(("Bookworm", "Read 50 books", "badge-gold"))
        if read_books >= 100:
            achievements.append(("Literary Legend", "Read 100 books", "badge-gold"))
        
        if avg_rating >= 4.5:
            achievements.append(("Critic's Choice", "Average rating 4.5+", "badge-gold"))
        elif avg_rating >= 4.0:
            achievements.append(("Well Read", "Average rating 4.0+", "badge-silver"))
        
        if unique_authors >= 20:
            achievements.append(("Diverse Reader", "Read from 20+ authors", "badge-silver"))
        elif unique_authors >= 10:
            achievements.append(("Explorer", "Read from 10+ authors", "badge-bronze"))
        
        series_counts = df[df['series'].notna() & (df['series'] != '')]['series'].value_counts()
        if any(series_counts >= 5):
            achievements.append(("Series Master", "Completed a series of 5+ books", "badge-gold"))
        elif any(series_counts >= 3):
            achievements.append(("Series Collector", "Collected 3+ books in a series", "badge-silver"))
        
        if achievements:
            st.markdown("<h3>Earned Badges</h3>", unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, (name, desc, badge_class) in enumerate(achievements):
                with cols[idx % 3]:
                    st.markdown(f"""
                        <div class="modern-card" style="text-align: center;">
                            <div class="badge {badge_class}" style="font-size: 1.5rem; margin-bottom: 0.5rem;">{name[0]}</div>
                            <strong>{name}</strong><br>
                            <span style="color: #666; font-size: 0.75rem;">{desc}</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Keep reading to unlock achievements! Read your first book to start.")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("<h3>Progress to Next Milestones</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            next_milestone = 10 if read_books < 10 else (25 if read_books < 25 else (50 if read_books < 50 else 100))
            if read_books < next_milestone:
                progress = read_books / next_milestone
                st.write(f"**Next Reading Milestone:** {next_milestone} books")
                st.progress(progress)
                st.caption(f"{read_books} of {next_milestone} books ({progress*100:.1f}%)")
        
        with col2:
            next_author_milestone = 10 if unique_authors < 10 else 20
            if unique_authors < next_author_milestone:
                progress = unique_authors / next_author_milestone
                st.write(f"**Next Author Milestone:** {next_author_milestone} authors")
                st.progress(progress)
                st.caption(f"{unique_authors} of {next_author_milestone} authors ({progress*100:.1f}%)")

# ==================== PAGE 7: LIBRARY ====================
else:
    st.markdown("<h1>Library</h1>", unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Browse your collection</p>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.info("Your library is empty. Add some books.")
    else:
        with st.expander("Filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.multiselect("Status", ["Read", "Unread"], default=["Read", "Unread"])
            with col2:
                format_filter = st.multiselect("Format", df['format'].unique(), default=df['format'].unique())
            with col3:
                author_filter = st.multiselect("Author", sorted(df['author'].unique()), default=[])
        
        filtered = df.copy()
        if "Read" not in status_filter:
            filtered = filtered[filtered['is_read'] == False]
        if "Unread" not in status_filter:
            filtered = filtered[filtered['is_read'] == True]
        if format_filter:
            filtered = filtered[filtered['format'].isin(format_filter)]
        if author_filter:
            filtered = filtered[filtered['author'].isin(author_filter)]
        
        st.caption(f"Showing {len(filtered)} of {len(df)} books")
        
        for _, book in filtered.iterrows():
            rating = reviews.get(f"{book['title']}_{book['author']}", 0)
            stars = "★" * rating + "☆" * (5 - rating) if rating > 0 else "Not rated"
            status_class = "status-read" if book['is_read'] else "status-unread"
            status_text = "Read" if book['is_read'] else "To Read"
            
            st.markdown(f"""
                <div class="modern-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <strong style="font-size: 1rem;">{book['title']}</strong>
                            <div style="color: #666; font-size: 0.8rem; margin-top: 4px;">{book['author']}</div>
                            <div style="margin-top: 8px;">
                                <span class="badge badge-gray">{book['format']}</span>
                                <span class="badge {status_class.replace('status-', 'badge-') if book['is_read'] else 'badge-gray'}">{status_text}</span>
                                {f'<span class="badge badge-gray">{book["series"]}</span>' if book['series'] else ''}
                            </div>
                            <div class="rating-stars" style="margin-top: 6px;">{stars}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        csv = filtered.to_csv(index=False)
        st.download_button("Export to CSV", csv, "library_export.csv", "text/csv", use_container_width=True)