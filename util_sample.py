import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import matplotlib.mlab as mlab
from util_MDN import *

def sample_theta(thetas):
	stop = np.random.rand()#random number to stop, [0,1]
	num_thetas = len(thetas)#should be mixtures
	cum = 0.0
	for i in range(num_thetas):
		cum+=thetas[i]
		if cum>stop:
			return i
	return 0

def sample_more(session, placeholder_x, initial_state, final_state, outputs, config, seq, predict_len=30, sl_pre = 4, bias=1.0, display=False, sample_until_landing=False, output_gaussian=False):
	assert seq.shape[0] == config['coords'], 'Feed a sequence in [crd,sl]'
	assert sl_pre > 1, 'Please provide two predefined coordinates' 

	state = session.run(initial_state)

	seq_feed = np.zeros((config['batch_size'], config['coords'], predict_len+1))
	seq_feed[0,:,:sl_pre+1] = seq[:,:sl_pre+1]
	gaussian_z = np.zeros((config['mixtures']*3, predict_len+1))
	draw_z = np.zeros((1, predict_len+1))

	for i in range(predict_len):
		feed_dict = {placeholder_x:seq_feed[:,:,i:i+1]}
		for j, (c, h) in enumerate(initial_state):
			feed_dict[c] = state[j][0]
			feed_dict[h] = state[j][1]
		result, state = session.run([outputs, final_state], feed_dict=feed_dict)

		idx_theta = sample_theta(result[7][0,:,0])
		mean = np.zeros((3))
		mean[0] = result[0][0,idx_theta,0]
		mean[1] = result[1][0,idx_theta,0]
		mean[2] = result[2][0,idx_theta,0]
		cov = np.zeros((3,3))
		s1 = np.exp(-1*bias)*result[3][0,idx_theta,0]
		s2 = np.exp(-1*bias)*result[4][0,idx_theta,0]
		s3 = np.exp(-1*bias)*result[5][0,idx_theta,0]
		s12 = result[6][0,idx_theta,0]*s1*s2
		cov[0,0] = np.square(s1)
		cov[1,1] = np.square(s2)
		cov[2,2] = np.square(s3)
		cov[1,0] = s12
		cov[0,1] = s12
		rv = multivariate_normal(mean, cov)
		draw = rv.rvs()
		if i>=sl_pre:
			seq_feed[0,:,i+1] = seq_feed[0,:,i] + draw
		draw_z[0,i+1] = draw[2]
		gaussian_z[:config['mixtures'],i+1] = result[2][0,:,0]#mean
		gaussian_z[config['mixtures']:config['mixtures']*2,i+1] = result[5][0,:,0]#std
		gaussian_z[config['mixtures']*2:,i+1] = result[7][0,:,0]#theta
		if i>sl_pre and sample_until_landing:
			if seq_feed[0,2,i+1]>seq_feed[0,2,i] and seq_feed[0,2,i]<seq_feed[0,2,i-1]:
				predict_len = i+2
				break
			if i==predict_len-1:
				#not found
				return None

	if display:
		fig = plt.figure()
		ax = fig.gca(projection='3d')
		ax.plot(seq[0,:], seq[1,:], seq[2,:],'r')
		ax.plot(seq_feed[0,0,:predict_len], seq_feed[0,1,:predict_len], seq_feed[0,2,:predict_len],'b')
		ax.set_xlabel('x coordinate')
		ax.set_ylabel('y coordinate')
		ax.set_zlabel('z coordinate')
		plt.show()

	if output_gaussian:
		return seq_feed[:,:,:predict_len], gaussian_z[:,:predict_len], draw_z
	return seq_feed[:,:,:predict_len]


def sample_next(session, placeholder_x, initial_state, final_state, outputs, config, seq, sl_pre = 4, bias=1.0, display=False):
	assert seq.shape[0] == config['coords'], 'Feed a sequence in [crd,sl]'
	assert sl_pre > 1, 'Please provide two predefined coordinates' 

	state = session.run(initial_state)

	seq_feed = np.zeros((config['batch_size'], config['coords'], seq.shape[1]))
	seq_feed[0,:,:] = seq[:,:]
	seq_pred = np.zeros((config['batch_size'], config['coords'], seq.shape[1]+1))
	seq_pred[0,:,:sl_pre+1] = seq[:,:sl_pre+1]

	for i in range(seq.shape[1]):
		feed_dict = {placeholder_x:seq_feed[:,:,i:i+1]}
		for j, (c, h) in enumerate(initial_state):
			feed_dict[c] = state[j][0]
			feed_dict[h] = state[j][1]
		result, state = session.run([outputs, final_state], feed_dict=feed_dict)

		idx_theta = sample_theta(result[7][0,:,0])
		mean = np.zeros((3))
		mean[0] = result[0][0,idx_theta,0]
		mean[1] = result[1][0,idx_theta,0]
		mean[2] = result[2][0,idx_theta,0]
		cov = np.zeros((3,3))
		s1 = np.exp(-1*bias)*result[3][0,idx_theta,0]
		s2 = np.exp(-1*bias)*result[4][0,idx_theta,0]
		s3 = np.exp(-1*bias)*result[5][0,idx_theta,0]
		s12 = result[6][0,idx_theta,0]*s1*s2
		cov[0,0] = np.square(s1)
		cov[1,1] = np.square(s2)
		cov[2,2] = np.square(s3)
		cov[1,0] = s12
		cov[0,1] = s12
		rv = multivariate_normal(mean, cov)
		draw = rv.rvs()
		if i>=sl_pre:
			seq_pred[0,:,i+1] = seq_feed[0,:,i] + draw

	if display:
		fig = plt.figure()
		ax = fig.gca(projection='3d')
		ax.plot(seq[0,:], seq[1,:], seq[2,:],'r')
		ax.plot(seq_pred[0,0,:], seq_pred[0,1,:], seq_pred[0,2,:],'b')
		ax.set_xlabel('x coordinate')
		ax.set_ylabel('y coordinate')
		ax.set_zlabel('z coordinate')
		plt.show()

	return seq_pred

def sample_next(session, placeholder_x, initial_state, final_state, outputs, config, seq, sl_pre = 4, bias=1.0, display=False):
	assert seq.shape[0] == config['coords'], 'Feed a sequence in [crd,sl]'
	assert sl_pre > 1, 'Please provide two predefined coordinates' 

	state = session.run(initial_state)

	seq_feed = np.zeros((config['batch_size'], config['coords'], seq.shape[1]))
	seq_feed[0,:,:] = seq[:,:]
	seq_pred = np.zeros((config['batch_size'], config['coords'], seq.shape[1]+1))
	seq_pred[0,:,:sl_pre+1] = seq[:,:sl_pre+1]

	for i in range(seq.shape[1]):
		feed_dict = {placeholder_x:seq_feed[:,:,i:i+1]}
		for j, (c, h) in enumerate(initial_state):
			feed_dict[c] = state[j][0]
			feed_dict[h] = state[j][1]
		result, state = session.run([outputs, final_state], feed_dict=feed_dict)

		idx_theta = sample_theta(result[7][0,:,0])
		mean = np.zeros((3))
		mean[0] = result[0][0,idx_theta,0]
		mean[1] = result[1][0,idx_theta,0]
		mean[2] = result[2][0,idx_theta,0]
		cov = np.zeros((3,3))
		s1 = np.exp(-1*bias)*result[3][0,idx_theta,0]
		s2 = np.exp(-1*bias)*result[4][0,idx_theta,0]
		s3 = np.exp(-1*bias)*result[5][0,idx_theta,0]
		s12 = result[6][0,idx_theta,0]*s1*s2
		cov[0,0] = np.square(s1)
		cov[1,1] = np.square(s2)
		cov[2,2] = np.square(s3)
		cov[1,0] = s12
		cov[0,1] = s12
		rv = multivariate_normal(mean, cov)
		draw = rv.rvs()
		if i>=sl_pre:
			seq_pred[0,:,i+1] = seq_feed[0,:,i] + draw

	if display:
		fig = plt.figure()
		ax = fig.gca(projection='3d')
		ax.plot(seq[0,:], seq[1,:], seq[2,:],'r')
		ax.plot(seq_pred[0,0,:], seq_pred[0,1,:], seq_pred[0,2,:],'b')
		ax.set_xlabel('x coordinate')
		ax.set_ylabel('y coordinate')
		ax.set_zlabel('z coordinate')
		plt.show()

	return seq_pred