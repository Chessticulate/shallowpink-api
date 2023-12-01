from app import crud

def test_password_hashing():
    pswd = "test password"

    pswd_hash = crud.hash_password(pswd)
    
    assert crud.check_password(pswd, pswd_hash) 

def test_get_user_by_name(init_fake_user_data, fake_user_data):
    for data in fake_user_data:
        user = crud.get_user_by_name(data["name"])
        #print(user[0], "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        assert user.email == data["email"]
        
