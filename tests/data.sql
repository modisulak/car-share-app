
INSERT INTO user (username, password,firstname,lastname,userType,email)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f','John','Kate','U','john@kate.com'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO car (make,model,body_type,colour,seats,lng,lat,cosePerHour)
VALUES
   ('Honda','Civic','Sedan','Black','5', '-2222222222','22222222','33');

INSERT INTO bookings (start_time,end_time)
VALUES
   ('23/05/2020','27/05/2020','1','1');   


