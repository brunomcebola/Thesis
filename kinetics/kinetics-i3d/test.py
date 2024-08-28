import tensorflow as tf

a = tf.Variable(0., name='a')
b = tf.Variable(0., name='b')
with tf.name_scope('scoped'):
  c = tf.Variable(0., name='c')
print("Initialized [a, b, c]: ", [a.numpy(), b.numpy(), c.numpy()])
saver = tf.train.Checkpoint(var_list=[a, b, c]).restore(save_path='tf1-ckpt-saved-in-eager')
print("Restored [a, b, c]: ", [a.numpy(), b.numpy(), c.numpy()])