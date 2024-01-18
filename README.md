## Dependencies:

- Flask: pip install https://github.com/mitsuhiko/flask/tarball/master
- mySQL: pip install mysql-connector-python
- Jinja2: pip install Jinja2
- Flask-Session: pip install Flask-Session
- Hashlib: pip install hashlib
- QRCode: pip install qrcode
- Report lab: pip install reportlab

---

## To run:
- Enter the main project directory
- flask --app=main run while in main directory
- Go to localhost:5000/127.0.0.1:5000/whatever you prefer to view the site (as of now)

- Distributed: run the bash file (or the distributed.py directly)
---

## Contributors:

- Nicholas Pena
- AJ Tello
- Yelena Trunina
- Daniel McDougall
- Jonas Wilson

## Sources
- QR-Code reader: https://www.npmjs.com/package/html5-qrcode
- security: https://www.securecoding.com/blog/flask-security-best-practices/
- Class slides
- Report lab: https://www.reportlab.com/docs/reportlab-userguide.pdf
- sql injection protection - https://mysql-python.sourceforge.net/MySQLdb.html#some-examples
---

## Proposal

Objective:
To create an online pass system for Florida State Parks that allows customers to purchase and manage their passes, as well as provide park rangers and county officials with the ability to manage and view sales reports.

System Features:

• Customer Login: Customers will be able to create an account and login to purchase passes for any state park in Florida. They will also be able to view their current and expired passes.
• Park Ranger Admin Role: The role will allow users to add and edit new parks and passes, create other users, and view sales reports for each county.

Technologies Used:
flask will be used to handle the backend functionality
Jinja will be used for template rendering
HTML/CSS will be used for the front-end design and layout
MySQL will be used as the database management system

Workload:
At the onset of the project, our team will be divided into specialized roles with AJ and Nicholas focusing on front-end development, Daniel and Jonas working on back-end development, and Yelena working on database development. As the project progresses, we anticipate forming groups of 2-3 individuals to work on specific features in all aspects of development.

---

## Exta features
• QR scanning
• PDF report generation

---

## Seperation of work
Disclaimer: A lot of this was paired or group programming, and all individuals were involved in most, if not all aspects of the project

• Register: Nick, Jonas
• Login: Nick, Jonas
• Generate and buy passes: AJ, Daniel
• Load passes: AJ, Yelena
• edit profile/password: Daniel, Jonas
• add admin/admin features: AJ, Nick
• distributed bash script setup: Nick, Jonas
• distributed python file: Nick, Jonas
• QR code: AJ
• PDF files: Yelena, Daniel
• Other reports: Yelena, Daniel 
• Database setup: Yelena

---
## Report on Role-Based Access

Background

For the Florida State Parks Project, we have decided to use MySQL and host it on AWS, and we
were planning to implement role-based access to manage user permissions. However, we encountered a problem while implementing this feature. The admin user provided by AWS during the initial setup did not have SUPER permissions, which prevented us from adding users to the groups we created.
Group Creation Initially, we created two groups: "park ranger" and "customer."
The park ranger group was supposed to have read, update, delete, and execute access, along with system access corresponding to park ranger.
Similarly, the customer group was meant to allow only read and update access and system access corresponding to the customer.

SUPER Permissions Issue

We faced difficulty adding users to these groups because we did not have SUPER permissions in
the database. We were hoping to create a user and assign them to a group, but unfortunately, that wasn't possible due to the lack of SUPER permissions. AWS doesn't provide SUPER permissions to the MySQL database by default for security reasons. SUPER permissions allow a user to perform tasks such as starting and stopping the database server, changing global system variables, and killing other users' sessions, and that is why AWS restricts those permissions.
Workaround Solution
To tackle this issue, we came up with a workaround. We created a column called "isAdmin" on
the Users table, which differentiated between park rangers and customers. We handled the isAdmin bit column on the Python side, where if the user was an admin, they would only have access to the admin pages, and if the user was a customer, they would only have access to the customer pages.

Future Considerations

While this workaround worked for us, we acknowledge that it's not an ideal solution. In future
projects, we plan to consider different hosts other than AWS to obtain SUPER permissions so that we can implement role-based access in a more streamlined manner.

Conclusion

In conclusion, we were unable to implement role-based access as planned due to the lack of
SUPER permissions provided by the AWS admin user. However, we found a workaround solution by creating a column on the Users table to differentiate between park rangers and customers. We plan to explore different hosting options in future projects to avoid this issue altogether.

---

