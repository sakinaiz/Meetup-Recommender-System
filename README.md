# Meetup-Recommender-System
A Recommender System for Meetup organizers to find synergies in similar groups or topics

**Synopsis**

Meetups are a great forum to meet like-minded people and to learn about new trends. Most big cities in the USA have multiple Meetups that cover similar topics, but many of these Meetups only have events once or twice a year. Organizers could benefit from joining forces to share costs and hence have more regular participants. More importantly, they could tap into the technical and organizational expertise of other organizers while avoiding logistical issues like a clash in event dates.

To address this issue I wanted to build a Recommender System (RS) for Meetup organizers to find synergies in similar groups. For my initial prototype, I obtained information about groups in San Francisco and New York with at least 20 members through the Meetup.com API. For each group, I queried the organizer ID, its category, age and location, the topics covered by it, and its member count. I then acquired the information about each of these group’s organizers and the events held by these groups. I built the data analysis pipeline using Python on AWS EC2.

I chose a hybrid RS for my problem since I had the utility matrix (user/item/rating tuple) and the item metadata. For this project, the “user" is the organizer, the “item” is the group, and for “ratings" I used an implicit proxy. I picked the Factorization Machines model which is a supervised machine learning technique and works great with large sparse datasets. It uses both the feature interactions and the group features. To build the system, I divided the data into cross-validation (CV) and holdout set, trained the model using the CV set, evaluated it using the RMSE metric and tested the final model on the holdout set. 

After putting in a considerable amount of effort, I realized that this model was not suitable for my dataset. My hypothesis for the failure of this model is two reasons. One, my dataset did not have sufficient “user”-“item" interactions, since most of the organizers hosted at most one group. Second, due to the lack of an explicit rating, I had to engineer one which was not a reliable target to predict by this model.

Since I wanted to recommend similar groups to organizers, I switched to a Content-based RS. I used categorical features like location and category, numerical features like age, member count, number of events and text features like the groups' topics of interest. Next, I applied SVD to extract the latent features. Finally, I used Euclidean distance as my dissimilarity metric. Using an unsupervised content-based method worked well because it helped bypass the need for target values as in FM.

Given a Meetup group, the RS then suggests an ordered list of 10 most similar groups to the organizer of the group. As next steps, bringing in the group’s members’ information would also be very interesting as I think there’s a potential for a lot of signal in this data.
