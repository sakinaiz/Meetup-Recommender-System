# Meetup-Recommender-System
A Recommender System for Meetup organizers to find synergies in similar groups or topics

**Synopsis**

Meetups are a great forum to meet like-minded people and to learn about new trends. Most big cities in the USA have multiple Meetups that cover similar topics, an excellent way to build the community. However, the problem is that most of these Meetups have events only once a year which defeats the purpose of organizing one. 

To address this issue I wanted to build a Recommender System (RS) for Meetup organizers to find synergies in similar groups. To build the system I collected the data using the Meetup API. For my initial prototype, I obtained information about groups in San Francisco and New York with at least 20 members. For each group, I queried the organizer ID, its category, age and location, the topics covered by it, and its member count. I then got the information about each of these group’s organizers and also about the events held by these groups. I built this system using Python and used AWS for my computation.

Most recommendation problems assume that we have a utility matrix (user/item/rating tuple) which is the basis of the Collaborative Filtering algorithms. For this project, the “user" is the group's organizer, the “item” is the Meetup group, and the “rating" is an implicit “likeness" score. In addition to this information, I also had plenty of ”user” and ”item" metadata that can be used to make better predictions. Hence, I chose the Factorization Machines model for my recommendation problem. It is a supervised machine learning technique and works great with large sparse datasets. It uses both the feature interaction and the group features. To build the model, I divided the data into cross-validation (CV) and holdout set, trained the model using the CV set and tested the final model on the holdout set. I used RMSE as the evaluation metric. 

After putting in a considerable amount of effort, I realized that this model was not suitable for my dataset. My hypothesis for the failure of this model is two reasons. One, my dataset did not have sufficient “user”-“item" interactions, since most of the organizers hosted at most one group. Second, due to the lack of an explicit rating, I had to engineer one which was not a reliable target to predict by this model.

Since I wanted to recommend similar groups to organizers, I switched to a Content-based RS. I used categorical features like location and category, numerical features like age, member count, number of events and text features like the groups' topics of interest. Next, I applied SVD to get the latent features. Finally, I used Euclidean distance as my dissimilarity metric. 

Given a Meetup group, the RS then suggests an ordered list of 10 most similar groups to the organizer of the group. As next steps, bringing in the group’s members’ information would also be very interesting as I think there’s a potential for a lot of signal in this data.
