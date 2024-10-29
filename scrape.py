from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import random

class LinkedInScraper:
    def __init__(self, email, password, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--disable-notifications')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.email = email
        self.password = password

    def login(self):
        try:
            print("Attempting to log in...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(3)
            
            # Login
            self.driver.find_element(By.ID, 'username').send_keys(self.email)
            self.driver.find_element(By.ID, 'password').send_keys(self.password)
            self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
            time.sleep(5)
            
            # Verify login success
            if "feed" in self.driver.current_url:
                print("Login successful!")
                return True
            print("Login may have failed - please check the browser")
            return False
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def wait_and_get_text(self, selector, wait_time=10):
        """Wait for element and get its text"""
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element.text.strip()
        except:
            return ""

    def scroll_to_bottom(self):
        """Scroll to bottom of page gradually"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down in smaller increments
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1) * last_height/3});")
                time.sleep(1)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            time.sleep(2)

    def expand_all_sections(self):
        """Click all show more buttons"""
        buttons = [
            "button.inline-show-more-text__button",
            "button.pv-profile-section__see-more-inline",
            ".pv-profile-section__see-more-inline",
            ".inline-show-more-text__button",
            ".pv-top-card-section__summary-toggle-button",
            "button.pv-profile-section__card-action-bar",
            ".pv-skills-section__additional-skills"
        ]
        
        for selector in buttons:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(1)
                    except:
                        continue
            except:
                continue

    def get_basic_info(self):
        """Get basic profile information"""
        print("Getting basic info...")
        selectors = {
            'name': [
                'h1.text-heading-xlarge',
                'h1.top-card-layout__title',
                '.pv-top-card--list li.inline'
            ],
            'headline': [
                '.text-body-medium',
                '.top-card-layout__headline',
                '.ph5.pb5 .mt2'
            ],
            'location': [
                '.top-card--list-bullet',
                '.top-card-layout__first-subline',
                '.pv-top-card--list.pv-top-card--list-bullet'
            ]
        }
        
        info = {}
        for field, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    value = self.wait_and_get_text(selector)
                    if value:
                        info[field] = value
                        print(f"Found {field}: {value}")
                        break
                except:
                    continue
            if field not in info:
                info[field] = ""
                print(f"Could not find {field}")
        
        return info

    def get_about(self):
        """Get about section"""
        print("Getting about section...")
        selectors = [
            "div.pv-shared-text-with-see-more full-width",
            "div.inline-show-more-text",
            "section.summary",
            ".pv-about-section",
            ".pv-about__summary-text"
        ]
        
        for selector in selectors:
            try:
                about = self.wait_and_get_text(selector)
                if about:
                    print("Found about section")
                    return about
            except:
                continue
        
        print("Could not find about section")
        return ""

    def get_experience(self):
        """Get work experience"""
        print("Getting experience...")
        experiences = []
        
        try:
            # Wait for experience section
            experience_section = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#experience-section, section.experience-section"))
            )
            
            # Get all experience items
            exp_items = experience_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
            
            for item in exp_items:
                try:
                    exp_data = {
                        'title': self.get_element_text(item, '.t-bold span, .t-16.t-black.t-bold'),
                        'company': self.get_element_text(item, '.t-14.t-normal, .pv-entity__secondary-title'),
                        'duration': self.get_element_text(item, '.pv-entity__date-range span:nth-child(2), .experience-item__duration'),
                        'location': self.get_element_text(item, '.pv-entity__location span:nth-child(2), .experience-item__location'),
                        'description': self.get_element_text(item, '.pv-entity__description, .experience-item__description')
                    }
                    
                    if exp_data['title'] or exp_data['company']:
                        experiences.append(exp_data)
                        print(f"Found experience: {exp_data['title']} at {exp_data['company']}")
                except Exception as e:
                    print(f"Error parsing experience item: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error in experience section: {str(e)}")
        
        print(f"Found {len(experiences)} experiences")
        return experiences

    def get_element_text(self, parent, selector):
        """Safely get element text"""
        try:
            element = parent.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""

    def get_education(self):
        """Get education information"""
        print("Getting education...")
        education = []
        
        try:
            # Find education section
            education_section = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#education-section, section.education-section"))
            )
            
            # Get all education items
            edu_items = education_section.find_elements(By.CSS_SELECTOR, ".pv-education-entity, .pv-profile-section__list-item")
            
            for item in edu_items:
                try:
                    edu_data = {
                        'school': self.get_element_text(item, '.pv-entity__school-name, .education__school-name'),
                        'degree': self.get_element_text(item, '.pv-entity__degree-name, .education__item--degree-info'),
                        'field': self.get_element_text(item, '.pv-entity__fos, .education__item--field-of-study'),
                        'dates': self.get_element_text(item, '.pv-entity__dates, .education__item--duration')
                    }
                    
                    if edu_data['school']:
                        education.append(edu_data)
                        print(f"Found education: {edu_data['school']}")
                except Exception as e:
                    print(f"Error parsing education item: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error in education section: {str(e)}")
        
        print(f"Found {len(education)} education entries")
        return education

    def get_skills(self):
        """Get skills"""
        print("Getting skills...")
        skills = []
        
        try:
            # Try to expand skills section
            try:
                show_more = self.driver.find_element(By.CSS_SELECTOR, ".pv-skills-section__additional-skills")
                self.driver.execute_script("arguments[0].click();", show_more)
                time.sleep(2)
            except:
                pass
            
            # Look for skills in multiple possible locations
            skill_selectors = [
                ".pv-skill-category-entity__name-text",
                ".pv-skill-category-entity__name",
                ".skill-category-entity__name"
            ]
            
            for selector in skill_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        skills = [skill.text.strip() for skill in elements if skill.text.strip()]
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"Error in skills section: {str(e)}")
        
        print(f"Found {len(skills)} skills")
        return skills

    def scrape_profile(self, profile_url):
        """Main method to scrape a profile"""
        try:
            print(f"\nAccessing profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(5)
            
            # Scroll and expand
            print("Scrolling through profile...")
            self.scroll_to_bottom()
            
            print("Expanding sections...")
            self.expand_all_sections()
            time.sleep(2)
            
            # Gather profile data
            profile_data = {
                'basic_info': self.get_basic_info(),
                'about': self.get_about(),
                'experience': self.get_experience(),
                'education': self.get_education(),
                'skills': self.get_skills()
            }
            
            return profile_data
            
        except Exception as e:
            print(f"Error scraping profile: {str(e)}")
            return None

    def save_results(self, results, output_file='linkedin_profiles.json'):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")

    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    # Your LinkedIn credentials
    EMAIL = "fopofa2394@nestvia.com"  
    PASSWORD = "WRITE YOUR PASSWORD HERE"       
    
    # Profile URLs to scrape
    PROFILE_URLS = [
        "https://www.linkedin.com/in/nicholas-battjes/"  # <-- Put profile URL here
    ]
    
    scraper = None
    try:
        # Initialize and login
        scraper = LinkedInScraper(EMAIL, PASSWORD)
        if not scraper.login():
            print("Failed to login. Exiting...")
            return
        
        # Scrape profiles
        results = []
        for url in PROFILE_URLS:
            print(f"\nScraping profile: {url}")
            profile_data = scraper.scrape_profile(url)
            if profile_data:
                results.append(profile_data)
            time.sleep(random.uniform(3, 7))
        
        # Save results
        if results:
            scraper.save_results(results)
            print("\nScraping completed successfully!")
        else:
            print("\nNo data was scraped successfully.")
            
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()