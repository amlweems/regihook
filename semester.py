#!/usr/bin/env python
# This is just an example!
# Customize this to fit your needs

semester = "fall"

auth = {
    'username': '<censored>',
    'password': '<censored>'
}

schedule = [
    {
        "course": "EE 379K",
        "uid": [ 16785 ],
        "failure": [ ]
    },
    {
        "course": "EE 360C",
        "uid": [ 16585 ],
        "failure": [ ]
    },
    {
        "course": "EE 464H",
        "uid": [ 16720, 16735, 16740, 16745, 16750 ],
        "failure": [
            {
                "course": "CMS 347K",
                "uid": [ 7435 ],
                "failure": [ ]
            }
        ]
    }
]

