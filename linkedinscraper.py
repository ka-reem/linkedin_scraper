from linkedin_scraper import Person, actions
from selenium import webdriver

# Setup the Chrome driver
driver = webdriver.Chrome()

# Login to LinkedIn first (required for most scraping)
email = "fopofa2394@nestvia.com"
password = "put your password here"
actions.login(driver, email, password)

# Now you can scrape a profile
person = Person("https://www.linkedin.com/in/nicholas-battjes/", driver=driver)


# Now you can access the data like this:
print("Name:", person.name)
print("Job Title:", person.job_title)
print("Company:", person.company)

print("\nExperiences:")
for experience in person.experiences:
    print("All experience data:")
    print(vars(experience))  # This will show all available attributes
    print()

driver.quit()



