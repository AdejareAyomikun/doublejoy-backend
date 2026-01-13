# DoubleJoy-Backend(E-commerce) API

## Endpoints

### Admin Endpoints
1. *Register Admin and User*
    - *POST* /api/auth/register/
      *Request Body:*
      json
      {
        "username": "Iyanuoluwa@2025",
        "email": "iyanuoluwaadejare@gmail.com",
        "password": "Daniel@2025",
        "first_name": "Iyanuoluwa",
        "last_name": "Adejare",
      }

2.  *Admin and User Login*
    - *POST* /api/auth/login/
      *Request Body*
      json{
        "username": "BigDaddy2025",
        "password": "Adejare2025",
      }

3.  *Category Upload*
    - *POST* /api/categories/
      *Request Body*
      json{
        "name": ""
      }
4.  *Existing categories are represented with there id number*
    - They are:
    1. Phones "12"
    2. Sneakers "13"
    3. Cars "14"
    4. Wrist Watches "15"
    5. Male Wears "16"
    6. Female Wears "17"
    7. Laptops "18"
    8. Polos "19"
5.  *Product Upload*
    - *POST* /api/products/
      *Request Body*
      json{
        "name": "IPhone 14 Pro",
        "price": 50000,
        "stock": 50,
        "category": id number,
        "description": "Premium performance with Dynamic Island, ProMotion display, and 48MP sensor",
        "image": "http://localhost:8000/media/products/iphone-14-pro.png",
      }

