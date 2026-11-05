==============================================================
# KENYA AIRWAYS - FLIGHT BOOKING MANAGEMENT SYSTEM
## Backend project using Python data structures
==============================================================


## 1. OVERVIEW
-----------
```
This is a command-line Python program that lets a Kenya Airways
administrator manage flight routes and the information attached
to them: prices, available seats and passenger ratings.

The project focuses on choosing and using the right Python data
structures (lists, tuples, dictionaries and sets) to store and
analyse flight data. It does not use a database or a web
framework.
```

## 2. FEATURES
-----------
1. Enter flight routes
   - Admin enters flights one at a time until typing 'quit'.
   - At least 10 routes are required. If the admin quits early,
     the program keeps asking for more until 10 are entered.

2. Set route prices
   - Admin enters a price for every flight route.

3. Set seats available
   - Admin enters the number of seats available per flight.

4. Record passenger ratings
   - Admin enters a rating from 1 to 5 for each flight route
     (decimals such as 3.5 are allowed).

5. Route summary
   - Prints every route with its price, seats and rating.
   - Builds a set of unique destinations.

6. Route analysis
   - A function returns four separate data structures:
       popular_routes       routes rated 3 or higher
       expensive_routes     routes priced above $500
       few_seats            routes with fewer than 10 seats
       unique_destinations  all distinct destinations


## 3. DATA STRUCTURES USED
-----------------------
flight_routes   LIST of TUPLES
    Each item is (flight_number, route).
    Example: [('KQ100', 'Nairobi to London'),
              ('KQ101', 'London to Nairobi')]
    Why: a list keeps the order of entry and allows growth
    until 'quit'. A tuple suits a fixed flight number + route
    pair that should not change.

route_price     DICTIONARY
    Maps flight number to price in US dollars.
    Example: {'KQ100': 850, 'KQ101': 790}

route_seats     DICTIONARY
    Maps flight number to seats available.
    Example: {'KQ100': 50, 'KQ101': 30}

route_ratings   DICTIONARY
    Maps flight number to passenger rating (1 to 5).
    Example: {'KQ100': 4, 'KQ101': 3.5}

unique_destinations   SET
    Contains each destination once, taken from the text after
    " to " in each route. Example: {'London', 'Nairobi', 'Dubai'}
    Why: a set removes duplicates automatically.

popular_routes, expensive_routes, few_seats
    Built from the dictionaries above, for example as lists of
    flight numbers or dictionaries of flight number to value.


## 4. REQUIREMENTS
---------------
- Python 3.8 or newer
- No external libraries needed (standard library only)

Check your version:
    python --version


## 5. HOW TO RUN
-------------
1. Save the program as main.py (or your chosen file name).
2. Open a terminal in the project folder.
3. Run:
       python main.py
4. Follow the prompts in this order:
   a. Enter flight routes (type 'quit' when finished, minimum 10)
   b. Enter the price for each route
   c. Enter the seats available for each route
   d. Enter the passenger rating for each route
5. The program prints the route summary and the analysis results.


## 6. SUGGESTED PROGRAM STRUCTURE
------------------------------
main.py

    get_flight_routes()
        Collects (flight_number, route) tuples until 'quit' and
        at least 10 items are stored. Returns flight_routes.

    get_route_prices(flight_routes)
        Returns route_price dictionary.

    get_route_seats(flight_routes)
        Returns route_seats dictionary.

    get_route_ratings(flight_routes)
        Returns route_ratings dictionary.

    get_unique_destinations(flight_routes)
        Returns a set of destinations.

    print_route_summary(flight_routes, route_price,
                        route_seats, route_ratings)
        Loops through the routes and prints all details.

    analyse_routes(flight_routes, route_price,
                   route_seats, route_ratings)
        Returns popular_routes, expensive_routes, few_seats,
        unique_destinations.

    main()
        Runs everything in order.

    if __name__ == "__main__":
        main()


## 7. INPUT RULES AND VALIDATION
-----------------------------
- Flight number: required, cannot be blank, must be unique.
  Stored in uppercase (e.g. kq100 becomes KQ100).
- Route format: "Origin to Destination"
  (e.g. Nairobi to Mombasa). Origin and destination must differ.
- Price: a positive number.
- Seats: a whole number, zero or more.
- Rating: a number from 1 to 5.
- Invalid input shows an error message and asks again; the
  program should not crash on bad input.
- Typing 'quit' (any letter case) ends route entry, but only
  once 10 or more routes have been entered.


## 8. SAMPLE RUN
-------------
Enter flight number (or 'quit'): KQ100
Enter route (e.g. Nairobi to London): Nairobi to London
Enter flight number (or 'quit'): quit
You have entered 1 route. At least 10 are required.
Enter flight number (or 'quit'):
...

Enter price for KQ100: 850
Enter seats available for KQ100: 50
Enter rating for KQ100 (1-5): 4

--- ROUTE SUMMARY ---
KQ100 | Nairobi to London | $850 | Seats: 50 | Rating: 4

--- ANALYSIS ---
Popular routes (rating >= 3):   ['KQ100', 'KQ101']
Expensive routes (> $500):      ['KQ100', 'KQ101']
Few seats (< 10):               ['KQ105']
Unique destinations:            {'London', 'Nairobi', 'Dubai'}


## 9. ASSUMPTIONS
--------------
- All prices are in US dollars.
- Every flight number entered in step 1 receives a price,
  seat count and rating.
- A route's destination is the text after " to " in the route
  string.
- "Popular" means a rating of 3 or higher (inclusive).
- "Expensive" means strictly above $500.
- "Few seats" means strictly fewer than 10 seats.
- Data is held in memory only and is lost when the program ends.


## 10. POSSIBLE IMPROVEMENTS
-------------------------
- Save and load data from a file (CSV or JSON).
- Move to a database with Flask and SQLAlchemy.
- Add admin login, roles and protected endpoints.
- Add booking, cancellation and passenger accounts.
- Add automated tests with unittest or pytest.


11. AUTHOR
----------
Name:    James Andaro, Lewis Karanu, Chris