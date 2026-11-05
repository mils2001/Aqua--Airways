
def test_bookings_require_login(client):
    response = client.get("/bookings")
    assert response.status_code == 401
 
 
def test_passenger_sees_only_their_own_bookings(
    client, passenger, other_passenger, passenger_headers, make_booking
):
    mine = make_booking(passenger)
    theirs = make_booking(other_passenger)
 
    response = client.get("/bookings", headers=passenger_headers)
    assert response.status_code == 200
 
    references = [b["booking_reference"] for b in response.get_json()]
    assert mine.booking_reference in references
    assert theirs.booking_reference not in references
 
 
def test_passenger_cannot_open_someone_elses_booking(
    client, other_passenger, passenger_headers, make_booking
):
    theirs = make_booking(other_passenger)
 
    response = client.get(f"/bookings/{theirs.id}", headers=passenger_headers)
    assert response.status_code in (403, 404)
 
 
def test_passenger_can_open_their_own_booking(
    client, passenger, passenger_headers, make_booking
):
    mine = make_booking(passenger)
 
    response = client.get(f"/bookings/{mine.id}", headers=passenger_headers)
    assert response.status_code == 200
    assert response.get_json()["booking_reference"] == mine.booking_reference
 