SearchDesk

Video demo: 
Author: Oleg Nikeshin
Location: Ulyanovsk, Russia
Date: 2025-12-31

SearchDesk is a small web application built with Flask and SQLite.  
The project demonstrates a simplified searchandising workflow: managing
products, defining search rules, and previewing how those rules affect
search result ranking.

The application requires authentication. After logging in, a user can
add products to a catalog, define rules for specific search queries, and
test how products are ranked for a given query.

Products can be boosted by different attributes such as brand, gender,
and category. Rules support two matching modes: exact match and contains
match. For each rule, products can also be pinned to fixed positions so
they always appear at the top of the ranking.

When a query is entered on the ranking page, the application selects the
most appropriate rule, applies pinned products first, calculates a score
for the remaining products, and sorts the results accordingly. Each row
includes a short explanation showing why a product received its score.

The project uses Python, Flask, SQLite, Jinja templates, and Bootstrap for
the user interface.

Project structure:
- app.py: main Flask application and routing logic
- helpers.py: database helper, authentication decorator, boost parsing
- templates/: HTML templates for all pages
- static/styles.css: custom styles
- data.db: SQLite database

AI tools were used in a limited way for UI layout ideas and for general
questions about SQLite schema design. All application logic and final
implementation were written by me.
