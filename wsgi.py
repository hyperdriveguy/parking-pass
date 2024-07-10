from app import app, scrape_and_update_data, scheduler_thread, scheduler

if __name__ == "__main__":
    scrape_and_update_data()  # Scrape data initially
    scheduler_thread.start()
    scheduler.enter(1800, 1, scrape_and_update_data)  # Schedule the next scrape in 30 minutes
    app.run()
    scheduler_thread.join()  # Wait for the scheduler to finish
