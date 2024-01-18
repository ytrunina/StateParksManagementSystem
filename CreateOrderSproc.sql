-- Yelena Trunina
-- Create Order Stored procedure

CREATE PROCEDURE CreateOrder (
  IN p_total DECIMAL(10, 2),
  IN p_userId INT,
  IN p_parkIds VARCHAR(255)
)

BEGIN
  DECLARE v_orderId INT;
  DECLARE v_orderDate DATETIME;
  DECLARE v_lastUpdated DATETIME;
  DECLARE v_currentDate DATE;
  DECLARE v_passId INT;
  DECLARE v_parkId INT;
  DECLARE v_startDate DATE;
  DECLARE v_endDate DATE;
  DECLARE v_done INT DEFAULT 0;
  DECLARE v_auditUser VARCHAR(255);
  DECLARE parkPrice DECIMAL(10,2);

  -- Set the current date
  SET v_currentDate = CURRENT_DATE(),
      v_orderDate = CURRENT_DATE(),
      v_auditUser = p_userId,
      v_lastUpdated = CURRENT_DATE();


  -- Start a transaction
  START TRANSACTION;


  -- Insert into Orders table
  INSERT INTO Orders (totalAmount, userId, orderDate, auditUser)
  VALUES (p_total, p_userId, v_orderDate, v_audituser);

  -- Get the generated orderId
  SET v_orderId = LAST_INSERT_ID();

  -- Loop through the parkIds and insert into OrderItems and CustomerPasses tables
  WHILE v_done = 0 DO
    -- Get the next parkId
    SET v_parkId = SUBSTRING_INDEX(p_parkIds, ',', 1);
    SET parkPrice = (select price from StateParks where id = v_parkId);
    -- Insert into OrderItems table
    INSERT INTO OrderItems (orderId, itemFee, userId, stateParkId, auditUser)
    VALUES (v_orderId, parkPrice, p_userId, v_parkId, v_auditUser);


    -- Get the generated orderItemId
    SET v_passId = LAST_INSERT_ID();

    -- Set the start and end dates for the CustomerPasses table
    SET v_startDate = v_currentDate;
    SET v_endDate = DATE_ADD(v_startDate, INTERVAL 1 YEAR);

    -- Insert into CustomerPasses table
    INSERT INTO CustomerPasses (orderId, userId, auditUser, lastUpdated, stateParkId, startDate, endDate)
    VALUES (v_orderId, p_userId, v_auditUser, v_lastUpdated, v_parkId, v_startDate, v_endDate);

    -- Remove the inserted parkId from the list
    SET p_parkIds = SUBSTRING(p_parkIds, LENGTH(v_parkId) + 2);

    -- Check if there are any parkIds left to insert
    IF LENGTH(p_parkIds) = 0 THEN
      SET v_done = 1;
    END IF;
  END WHILE;
  -- Commit the transaction
  COMMIT;
END
